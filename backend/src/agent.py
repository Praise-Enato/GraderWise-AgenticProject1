"""LangGraph grading workflow for the Business Plan Grader.

This is thin orchestration over tested pure modules:
- llm.get_llm(task)            -> model router (no more duplicated client config)
- grading.parse_grader_response -> parse-fail safe grade data (graded_ok, never a silent 0)
- eligibility.screen_eligibility -> first-round DQ / AI-content screen
- grading.to_grade_result       -> API result carrying per-criterion assessments + status

Flow:

    prepare (eligibility + optional RAG)
        -> grade  -> validate --valid--> feedback -> END
                        ^                    |
                        +--- invalid, < max --+   (Judge: structural checks only)

Key decisions from the reviews:
- RAG is skipped by default (business plans have no corpus); the judges' GUIDELINE
  is injected as fixed context in the grader prompt instead.
- The fabricated confidence value is NOT injected into thinking_process; it is
  carried on GradeResult.confidence_score with a "not calibrated" caveat.
- The Judge does structural validation only (graded_ok, score bounds). The old
  academic keyword heuristics never fired on business rationale, so they're gone.
- Judge retries are configurable (state['max_retries']): capped for batch runs,
  full for the live single-plan demo.
"""
from dotenv import load_dotenv
import os
import datetime
import logging
from typing import List, TypedDict, Any, Optional

from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate

from functools import lru_cache

from backend.src.models import RubricItem, GradeResult, ELIGIBILITY_ELIGIBLE
from backend.src import rag
from backend.src import calibration
from backend.src import reference_corpus
from backend.src.llm import get_llm
from backend.src.grading import (
    GradeData,
    parse_grader_response,
    to_grade_result,
    find_missing_criteria,
    summarize_performance,
    aggregate_grade_data,
    DEFAULT_ENSEMBLE_N,
    DEFAULT_ENSEMBLE_TEMPERATURE,
    run_ensemble,
    unsupported_evidence,
)
from backend.src import business_name as _bname
from backend.src.eligibility import screen_eligibility
from backend.src.injection import detect_injection

load_dotenv()


@lru_cache(maxsize=1)
def _load_fewshot_examples():
    """Load few-shot calibration examples (empty list if none configured)."""
    path = os.getenv("BPC_FEWSHOT_PATH", "backend/data/bpc/few_shot_examples.json")
    try:
        return calibration.load_examples(path)
    except Exception as e:  # pragma: no cover - defensive
        print(f"few-shot load error: {e}")
        return []

# --- Logging ---------------------------------------------------------------- #
os.makedirs("backend/logs", exist_ok=True)
logging.basicConfig(
    filename="backend/logs/grading_debug.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True,
)
logger = logging.getLogger(__name__)


def log_agent_action(node_name: str, message: str, details: Any = None):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {node_name}: {message}")
    logger.info(f"{node_name}: {message}")
    if details is not None:
        logger.info(f"DETAILS: {details}")


DEFAULT_MAX_RETRIES = 3


# --- State ------------------------------------------------------------------ #
class AgentState(TypedDict, total=False):
    submission_files: List[dict]      # [{filename, content}]
    rubric: List[RubricItem]
    guideline: str                    # judges' guideline, injected as fixed context
    context: List[str]                # RAG context (empty when skip_rag)
    grade_data: GradeData
    final_feedback: str
    grade_result: GradeResult
    revision_number: int
    grader_feedback: str              # Judge's rejection reason, fed back to the grader
    is_valid: bool
    skip_rag: bool                    # default True for business plans (no corpus)
    max_retries: int                  # batch caps this low; live uses full
    thinking_process: List[str]
    eligibility: dict                 # {status, reasons, advisory_notes, ai_content_flag}
    use_calibration: bool             # competition mode: gates BYUMS eligibility screen + few-shot calibration
                                      # (default True). False = general rubric. MUST be declared here or
                                      # StateGraph drops it from the input and the gates never fire.
    use_grounding: bool               # retrieve the static grounding corpus into grader context (default
                                      # False; degrades to no-op if the corpus/embedding model is absent).
    use_evidence: bool                # ask the grader for a verbatim evidence quote per criterion and have
                                      # the Judge reject hallucinated quotes (default False; opt-in until the
                                      # eval gate passes, so /grade behavior is unchanged).
    ensemble_n: int                   # grade N times and aggregate per-criterion by median (default 1 =
                                      # single pass, current behavior).
    ensemble_temperature: float       # fixed sampling temperature for ensemble runs (X1: a single moderate
                                      # temperature, NOT a spread; default 0.4). Ignored when ensemble_n <= 1.


# --- Helpers ---------------------------------------------------------------- #
def _assemble_submission(submission_files: List[dict], max_len_per_file: int = 20000):
    """Return (prompt_formatted_text, combined_raw_text)."""
    formatted = ""
    combined_parts = []
    for f in submission_files:
        content = f.get("content", "") or ""
        combined_parts.append(content)
        shown = content
        if len(shown) > max_len_per_file:
            shown = shown[:10000] + "\n...[SNIP]...\n" + shown[-10000:]
        formatted += f"\n--- FILE: {f.get('filename', 'submission')} ---\n{shown}\n"
    return formatted, "\n".join(combined_parts)


def _format_rubric(rubric: List[RubricItem]) -> str:
    parts = []
    for i, item in enumerate(rubric):
        part = f"### CRITERION {i + 1}: {item.criteria} (Max: {item.max_points} pts)"
        if item.course_guide:
            part += f"\n   - [WHAT THIS MEANS]: {item.course_guide}"
        part += f"\n   - [FULL MARKS]: {item.description}"
        if item.developing_description:
            part += f"\n   - [PARTIAL]: {item.developing_description}"
        if item.zero_description:
            part += f"\n   - [ZERO/MISSING]: {item.zero_description}"
        parts.append(part)
    return "\n\n".join(parts)


def _rag_query(rubric: List[RubricItem]) -> str:
    topics = [item.criteria for item in rubric]
    details = [item.description for item in rubric]
    return (f"Context and definitions for: {', '.join(topics)}. {' '.join(details)}")[:2000]


def _confidence_from_revisions(revisions: int) -> float:
    # NOTE: heuristic only, not calibrated to correctness. Carried on GradeResult
    # but never presented to users as a real confidence value.
    if revisions == 1:
        return 0.99
    if revisions == 2:
        return 0.90
    if revisions >= 3:
        return 0.75
    return 0.95


# --- Prompts ---------------------------------------------------------------- #
GRADER_SYSTEM = """__GRADER_INTRO__ Evaluate the SUBMISSION
against the RUBRIC one criterion at a time. Weigh genuine potential for success, not polish.

CRITICAL — EVIDENCE AND TEXT-ONLY:
- You are given the submission's EXTRACTED TEXT ONLY. You CANNOT see images, slides, charts,
  tables, photos, videos, or scanned pages.
- Grade strictly on evidence ACTUALLY PRESENT in the text. If a criterion depends on content
  that is not in the text — including when only a slide TITLE or HEADING appears without the
  actual content beneath it (e.g. a "Financials" or "Business Registration" heading with no
  figures or details in the text) — award 0. NEVER assume content exists from a heading,
  label, or section title.

SCORING RULES:
1. The Rubric is Law. Score ONLY against the listed criteria, each independently.
2. Award FULL marks ONLY when the specific required element is fully and clearly present.
3. Award PARTIAL marks ONLY when the specific required element is genuinely, partially present.
4. Award 0 when the specific required element is ABSENT — even if the submission includes
   RELATED or ADJACENT content. Adjacent content is NOT credit. (Example: listing competitors
   is NOT "examples of what others are doing to solve the problem" — award 0 for that criterion,
   not partial.)
5. When uncertain between two tiers, choose the LOWER one. Do not be generous.
6. Explicit scoring. If a criterion specifies point values, use those exact numbers.
7. Local context. Do not penalize a business for operating in a developing local market; judge
   potential within its own context. This is about fairness of judgement, NOT a reason to inflate.
8. Data credibility. If quantitative data is internally inconsistent, incoherent, or impossible
   (totals that don't add up, profit exceeding revenue, contradictory figures), treat it as NOT
   credible and award little or no credit — wrong numbers signal a mistake or misrepresentation,
   and a table's mere presence is not evidence.
9. Evidence source. Evidence may be FIRST-HAND / primary — the team's own observations, customer
   counts, sales records, or informal surveys (e.g. "85 of 100 people I asked prefer X"). It does
   NOT need to be a formal or external source, but first-hand / unsourced figures earn only MODEST
   partial credit — not the full marks reserved for well-evidenced claims, and not zero. Vague
   claims with no specifics still earn little or nothing.
10. Do CREDIT elements that are clearly present. If a required element genuinely appears (e.g.
    competitors are named), award real marks for it — do not zero something that exists.
11. Follow the JUDGES' GUIDELINE below, and CALIBRATE your severity to the CALIBRATION REFERENCE
    (an expert judge's scored example) when one is provided.

SCORING DISPOSITION (how expert human graders actually score — apply to every criterion):
- Use the FULL range. Do not cluster awards in the safe middle. A criterion that is fully,
  clearly met earns FULL marks; one that is absent or unsupported earns 0. Both extremes are
  correct and expected when the evidence warrants them.
- No "pity points." Do not award a soft partial to be nice. Absent, vague, or unsupported
  content (e.g. financials with no basis, a "no competition" claim, a hand-wavy risk section)
  is 0, not 1.
- Be hardest on FINANCIALS and RISK. These are where weak plans are most often over-credited:
  demand concrete, internally consistent figures and specific, mitigated risks; otherwise score low.
- COMPLETENESS: you MUST return exactly one assessment object for EVERY rubric criterion, in order.
  Never omit a criterion; if it is absent from the submission, still include it with awarded_points 0.

BUSINESS NAME: also report the actual NAME OF THE BUSINESS this plan is for, exactly as
  the plan states it. This is the trading name of the venture — NOT the document's title,
  NOT a heading like "BUSINESS PLAN" or "Business Work Plan", NOT a slogan or tagline, and
  NOT a person's name unless the business genuinely trades under it. A title page may be
  wrong or generic while the real name appears in the executive summary or company
  overview; prefer the name the plan uses to refer to itself throughout. Use "" if the
  plan never names the business.

OUTPUT FORMAT — return a single JSON object (one assessment PER criterion, all of them):
{{
    "business_name": "<the venture's actual name, or \"\" if the plan never states it>",
    "assessments": [
        {{
            "criteria_index": 1,
            "criteria_name": "<name of the criterion>",
            "awarded_points": <number>,
            "reason": "<justification citing the rubric line matched or the evidence in the plan>"
        }}
    ],
    "general_feedback": "<one-paragraph overall summary>"
}}
"""

GRADER_USER = """{prior_feedback}RUBRIC:
{rubric_str}

JUDGES' GUIDELINE (apply to every criterion; if empty, use the rubric alone):
{guideline}

{calibration}

ADDITIONAL CONTEXT (optional, may be empty):
{context_str}

SUBMISSION:
{submission}
"""

FEEDBACK_SYSTEM = """__FEEDBACK_INTRO__

RULES (from the judging guidelines):
- Be positive AND constructive. Encourage, but give real, specific guidance.
- Write directly to the team ("you" / "your business"). They will read this.
- __FEEDBACK_VOCAB__
- Do NOT use slang, idioms, or business jargon/acronyms. If you must use a term, explain it plainly.
- Be specific. No one-line "good job" feedback. Name concrete strengths and concrete improvements.
- Give at least one concrete idea that could strengthen the business.
- You may state things directly (this is judge feedback, not a quiz). Do not withhold guidance.

OUTPUT FORMAT (Markdown):

**What you did well:**
[specific strengths, tied to the criteria]

**Where you can improve:**
[specific areas, tied to the criteria where points were lost]

**Ideas to strengthen your business:**
[concrete, encouraging suggestions and questions to consider]
"""

FEEDBACK_USER = """SUBMISSION:
{submission}

SCORE: {score} / {total_points}

PER-CRITERION RESULTS:
{rubric_performance}

CRITIQUE NOTES:
{critique}

STRONGEST CRITERIA (scored 80%+ of max — ground "what you did well" in these):
{strengths}

WEAKEST CRITERIA (scored below 60% of max — ground "where you can improve" in these):
{gaps}

Write the participant-facing feedback now.
"""


# --- Mode-specific prompt framing ------------------------------------------- #
# The shared grader/feedback prompts carry BYUMS-competition framing (prize money,
# "competition", non-native-English participants). That framing is correct in
# competition mode but is factually WRONG for the general rubric (an arbitrary
# business plan is not in a prize competition). We swap only the framing sentences
# by mode; the rules/output-format below them are universal. Placeholders are plain
# tokens (not {braces}) so ChatPromptTemplate never treats them as variables.
_GRADER_INTRO = {
    True: ("You are a STRICT, skeptical evaluator for a Business Plan Competition that "
           "awards real prize money. Over-scoring a weak plan is a serious error."),
    False: ("You are a STRICT, skeptical evaluator of business plans. Over-scoring a weak "
            "plan is a serious error."),
}
_FEEDBACK_INTRO = {
    True: ("You are a competition judge writing feedback directly to a participant team.\n\n"
           "In this competition, your written feedback is, in most cases, the ONLY prize a "
           "participant takes home. Make it genuinely useful."),
    False: ("You are an experienced business advisor writing feedback directly to the plan's "
            "author.\n\nYour written feedback is the most valuable thing they take away from "
            "this review. Make it genuinely useful."),
}
_FEEDBACK_VOCAB = {
    True: "Use simple vocabulary. English is not the first language for most participants.",
    False: "Use clear, simple vocabulary and avoid unnecessary jargon.",
}


_EVIDENCE_CLAUSE = """

EVIDENCE FIELD (REQUIRED THIS RUN):
For every criterion, add an "evidence" field to the JSON object: the EXACT,
VERBATIM quote copied from the SUBMISSION text that justifies the award (max
~200 characters). Copy it character-for-character; do NOT paraphrase, summarize,
or invent. If nothing in the submission text supports the award, set "evidence"
to an empty string "". A quote that does not appear in the submission will be
rejected."""


def grader_system(competition: bool = True, include_evidence: bool = False) -> str:
    """Resolve GRADER_SYSTEM for competition (True) or general (False) mode.

    include_evidence appends the evidence-quote instruction (opt-in): with it
    False the prompt is unchanged, so `/grade` behaves exactly as before."""
    prompt = GRADER_SYSTEM.replace("__GRADER_INTRO__", _GRADER_INTRO[bool(competition)])
    if include_evidence:
        prompt = prompt + _EVIDENCE_CLAUSE
    return prompt


def feedback_system(competition: bool = True) -> str:
    """Resolve FEEDBACK_SYSTEM for competition (True) or general (False) mode."""
    return (FEEDBACK_SYSTEM
            .replace("__FEEDBACK_INTRO__", _FEEDBACK_INTRO[bool(competition)])
            .replace("__FEEDBACK_VOCAB__", _FEEDBACK_VOCAB[bool(competition)]))


# --- Nodes ------------------------------------------------------------------ #
def prepare(state: AgentState) -> dict:
    """Screen eligibility and (optionally) retrieve RAG context. RAG is skipped by
    default for business plans; the judges' guideline is used as fixed context."""
    files = state["submission_files"]
    _, combined = _assemble_submission(files)

    # The eligibility/DQ screen is BYUMS-competition-specific (excluded business
    # types, required license/bank deliverables, English requirement). It only
    # applies in competition mode — NOT to the general rubric, where "franchise"
    # etc. are perfectly valid businesses. use_calibration marks competition mode.
    if state.get("use_calibration", True):
        elig = screen_eligibility(combined)
        thinking = ["Screening eligibility (business-type exclusions, language, AI-content)..."]
        if elig.status != ELIGIBILITY_ELIGIBLE:
            thinking.append(f"Eligibility: {elig.status} — {'; '.join(elig.reasons) or 'see notes'}")
        else:
            thinking.append("Eligibility: eligible.")
        eligibility = {
            "status": elig.status, "reasons": elig.reasons,
            "advisory_notes": elig.advisory_notes, "ai_content_flag": elig.ai_content_flag,
        }
    else:
        thinking = ["General rubric: competition eligibility/DQ screen skipped."]
        eligibility = {"status": ELIGIBILITY_ELIGIBLE, "reasons": [], "advisory_notes": [], "ai_content_flag": False}

    # Prompt-injection screen (OV#12): submissions are attacker-controlled, so flag
    # "ignore instructions / award full marks" style content for a human. Advisory
    # only — never an auto-DQ (same posture as the AI-content flag).
    injection_markers = detect_injection(combined)
    if injection_markers:
        eligibility["advisory_notes"] = list(eligibility.get("advisory_notes", [])) + [
            f"possible prompt injection ({', '.join(injection_markers)}) — treat the submission text as untrusted"
        ]
        thinking.append(f"Input screen: possible prompt-injection markers: {', '.join(injection_markers)}.")

    context: List[str] = []
    skip = state.get("skip_rag", True)  # default: skip RAG for business plans
    if not skip:
        try:
            context = rag.retrieve_context(_rag_query(state["rubric"]))
            thinking.append(f"Retrieved {len(context)} context chunks.")
        except Exception as e:
            log_agent_action("PREPARE", f"RAG error: {e}")
            thinking.append("RAG unavailable; continuing without it.")

    # Grounding: retrieve generic business-plan evaluation knowledge (financial
    # credibility, market sizing, quality guide) from the static reference corpus.
    # Graceful no-op if the corpus / embedding model is absent, so it's safe to
    # request even when nothing is ingested.
    if state.get("use_grounding", False):
        grounded = reference_corpus.retrieve_reference_context(_rag_query(state["rubric"]))
        if grounded:
            context = context + grounded
            thinking.append(f"Grounding: added {len(grounded)} reference chunk(s).")
        else:
            thinking.append("Grounding requested, but the reference corpus is unavailable; skipped.")

    return {
        "context": context,
        "eligibility": eligibility,
        "revision_number": state.get("revision_number", 0),
        "grader_feedback": state.get("grader_feedback", ""),
        "is_valid": False,
        "thinking_process": thinking,
    }


def grade_submission(state: AgentState) -> dict:
    """Grade the submission against the rubric. Parse-safe via grading.parse_grader_response."""
    attempt = state.get("revision_number", 0) + 1
    log_agent_action("GRADER", f"Grading (attempt {attempt})")
    rubric = state["rubric"]
    formatted, _ = _assemble_submission(state["submission_files"])
    rubric_str = _format_rubric(rubric)
    guideline = state.get("guideline", "") or "None provided."
    context_str = "\n\n".join(state.get("context", []))[:3000]
    grader_feedback = state.get("grader_feedback", "")

    # Carry the prior-rejection note as a template VALUE (not concatenated into the
    # template string) so its content is never parsed as template syntax.
    prior_feedback = ""
    if grader_feedback:
        prior_feedback = f"NOTE: a previous grade was rejected: {grader_feedback}. Fix this.\n\n"

    # Few-shot calibration. Exclude any example that IS the current submission
    # (leave-one-out) so a plan is never calibrated against itself (no leakage).
    # Skipped entirely when use_calibration is False (e.g. the general rubric, whose
    # criteria differ from the BYUMS example's).
    calibration_block = ""
    if state.get("use_calibration", True):
        submission_names = {f.get("filename", "") for f in state["submission_files"]}
        calibration_block = calibration.build_calibration_block(
            _load_fewshot_examples(), exclude_filenames=submission_names
        )

    system_prompt = grader_system(
        competition=state.get("use_calibration", True),
        include_evidence=state.get("use_evidence", False),
    )
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("user", GRADER_USER)])
    invoke_inputs = {
        "prior_feedback": prior_feedback,
        "rubric_str": rubric_str,
        "guideline": guideline,
        "calibration": calibration_block,
        "context_str": context_str,
        "submission": formatted,
    }

    def _run_once(temperature: float) -> GradeData:
        llm = get_llm("grade", temperature=temperature).bind(response_format={"type": "json_object"})
        response = (prompt | llm).invoke(invoke_inputs)
        return parse_grader_response(response.content, rubric)

    n = max(1, int(state.get("ensemble_n", DEFAULT_ENSEMBLE_N)))
    try:
        if n == 1:
            grade_data = _run_once(0.0)  # single deterministic pass — unchanged default behavior
        else:
            # X1: a fixed MODERATE temperature x N (not a temperature spread); the
            # disagreement across samples is the signal, aggregated by median.
            temp = float(state.get("ensemble_temperature", DEFAULT_ENSEMBLE_TEMPERATURE))
            # Concurrent: n times the tokens, ~one call's wall-clock (see run_ensemble).
            grade_data = aggregate_grade_data(run_ensemble(lambda: _run_once(temp), n))
        log_agent_action("GRADER", f"score={grade_data.score} graded_ok={grade_data.graded_ok} runs={n}")
    except Exception as e:
        log_agent_action("GRADER", f"grader call failed: {e}")
        grade_data = GradeData(score=0.0, graded_ok=False, error=f"Grader call failed: {e}")

    note = f"Graded {len(state['submission_files'])} file(s); score={grade_data.score}."
    if n > 1:
        note += f" (ensemble of {n}, median-aggregated)"
    return {
        "grade_data": grade_data,
        "thinking_process": state.get("thinking_process", []) + [note],
    }


def validate_grade(state: AgentState) -> dict:
    """Judge — structural validation: graded_ok + score bounds + rubric completeness.
    Pure Python, no LLM. Rejects to the Grader (up to MAX_RETRIES) on failure."""
    gd: GradeData = state["grade_data"]
    rubric = state["rubric"]
    total_points = sum(item.max_points for item in rubric)
    current = state.get("revision_number", 0)

    valid = True
    reason = ""
    if not gd.graded_ok:
        valid, reason = False, gd.error or "grade failed to parse"
    elif gd.score > total_points + 1e-9:
        valid, reason = False, f"score {gd.score} exceeds max possible {total_points}"
    elif gd.score < 0:
        valid, reason = False, f"score {gd.score} is negative"
    else:
        # Completeness: a single grader call can silently drop criteria on a long
        # rubric, giving an artificially low total that passes the bounds checks.
        missing = find_missing_criteria(gd.assessments, rubric)
        if missing:
            shown = "; ".join(missing[:8]) + ("; ..." if len(missing) > 8 else "")
            valid, reason = False, (
                f"incomplete grade: {len(missing)} of {len(rubric)} criteria were not scored "
                f"(missing: {shown}). Return exactly one assessment for EVERY criterion; "
                f"award 0 for any that are absent — do not omit them."
            )
        elif state.get("use_evidence", False):
            # Evidence guard (OV#7): reject a grade whose evidence quotes are not
            # actually in the submission, so "evidence-linked" feedback can't cite
            # hallucinated text. Uses the fuzzy matcher, so OCR/quote drift is tolerated.
            _, combined = _assemble_submission(state["submission_files"])
            bad = unsupported_evidence(gd.assessments, combined)
            if bad:
                shown = ", ".join(bad[:8]) + ("; ..." if len(bad) > 8 else "")
                valid, reason = False, (
                    f"unsupported evidence: the quote(s) for [{shown}] do not appear in the "
                    f"submission. Copy the EXACT text from the submission for each criterion's "
                    f"evidence, or set evidence to an empty string."
                )

    if valid:
        log_agent_action("JUDGE", "grade validated")
        return {
            "is_valid": True,
            "grader_feedback": "",
            "revision_number": current,
            "thinking_process": state.get("thinking_process", []) + ["Judge: grade validated."],
        }
    log_agent_action("JUDGE", f"grade rejected: {reason}")
    return {
        "is_valid": False,
        "grader_feedback": reason,
        "revision_number": current + 1,
        "thinking_process": state.get("thinking_process", []) + [f"Judge: rejected ({reason}); retrying."],
    }


def generate_feedback(state: AgentState) -> dict:
    """Produce BYUMS-voice participant feedback and assemble the final GradeResult."""
    gd: GradeData = state["grade_data"]
    rubric = state["rubric"]
    total_points = sum(item.max_points for item in rubric)
    elig = state.get("eligibility", {})
    revisions = state.get("revision_number", 0)
    confidence = _confidence_from_revisions(revisions)
    # NOTE: confidence is intentionally NOT appended to thinking_process.
    _voice = "BYUMS voice" if state.get("use_calibration", True) else "business-advisor voice"
    thinking = state.get("thinking_process", []) + [f"Writing participant feedback ({_voice})."]

    dq_reasons = list(elig.get("reasons", [])) + [
        f"(advisory) {n}" for n in elig.get("advisory_notes", [])
    ]

    # The business name comes from the plan itself, never the uploaded file name —
    # it heads the on-screen result and the downloadable PDF report. Read here
    # (rather than in the grader node) so a failed grade is still attributable.
    #
    # The GRADER's reading wins when it is trustworthy: it read the whole plan, so it
    # can name a venture whose title page is a slogan or is simply wrong. from_model
    # gates that on plausibility + actually appearing in the submission, and returns
    # nothing when it doesn't — then the deterministic reader takes over.
    _, _raw_submission = _assemble_submission(state["submission_files"])
    detected = (_bname.from_model(gd.business_name, _raw_submission)
                or _bname.extract(_raw_submission))
    if detected:
        thinking.append(f'Business name read from the plan: "{detected.name}" ({detected.source}).')

    if not gd.graded_ok:
        feedback = ("This submission could not be graded automatically and has been flagged "
                    "for human review. No score has been assigned.")
        result = to_grade_result(
            gd, feedback, thinking_process=thinking, confidence_score=confidence,
            eligibility_status=elig.get("status", ELIGIBILITY_ELIGIBLE),
            dq_reasons=dq_reasons, ai_content_flag=elig.get("ai_content_flag", False),
            business_name=detected.name,
        )
        return {"final_feedback": feedback, "grade_result": result, "thinking_process": thinking}

    formatted, _ = _assemble_submission(state["submission_files"], max_len_per_file=15000)
    rubric_perf = "\n".join(f"- {k}: {v}" for k, v in gd.rubric_performance.items())
    critique = "\n".join(f"- {c}" for c in gd.critique_points) or "None."

    # Strengths/gaps are derived DETERMINISTICALLY from the per-criterion scores (not
    # asked of the LLM) so the feedback is anchored to what was actually scored well/poorly.
    strengths, gaps = summarize_performance(gd.assessments)
    strengths_str = "\n".join(f"- {s}" for s in strengths) or "None scored at 80%+ of max."
    gaps_str = "\n".join(f"- {g}" for g in gaps) or "None scored below 60% of max."

    system_prompt = feedback_system(competition=state.get("use_calibration", True))
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("user", FEEDBACK_USER)])
    try:
        response = (prompt | get_llm("feedback")).invoke({
            "submission": formatted,
            "score": gd.score,
            "total_points": total_points,
            "rubric_performance": rubric_perf,
            "critique": critique,
            "strengths": strengths_str,
            "gaps": gaps_str,
        })
        feedback = response.content
    except Exception as e:
        log_agent_action("FEEDBACK", f"feedback generation failed: {e}")
        feedback = ("We were unable to generate detailed feedback automatically. "
                    "Please review the per-criterion results above.")

    result = to_grade_result(
        gd, feedback, thinking_process=thinking, confidence_score=confidence,
        eligibility_status=elig.get("status", ELIGIBILITY_ELIGIBLE),
        dq_reasons=dq_reasons, ai_content_flag=elig.get("ai_content_flag", False),
        business_name=detected.name,
    )
    return {"final_feedback": feedback, "grade_result": result, "thinking_process": thinking}


# --- Conditional edge ------------------------------------------------------- #
def check_validation(state: AgentState) -> str:
    if state.get("is_valid", False):
        return "generate_feedback"
    max_retries = state.get("max_retries", DEFAULT_MAX_RETRIES)
    if state.get("revision_number", 0) < max_retries:
        return "grade_submission"
    log_agent_action("GRAPH", "max retries reached; proceeding with best effort")
    return "generate_feedback"


# --- Build graph ------------------------------------------------------------ #
workflow = StateGraph(AgentState)
workflow.add_node("prepare", prepare)
workflow.add_node("grade_submission", grade_submission)
workflow.add_node("validate_grade", validate_grade)
workflow.add_node("generate_feedback", generate_feedback)

workflow.set_entry_point("prepare")
workflow.add_edge("prepare", "grade_submission")
workflow.add_edge("grade_submission", "validate_grade")
workflow.add_conditional_edges(
    "validate_grade",
    check_validation,
    {"grade_submission": "grade_submission", "generate_feedback": "generate_feedback"},
)
workflow.add_edge("generate_feedback", END)

app = workflow.compile()
