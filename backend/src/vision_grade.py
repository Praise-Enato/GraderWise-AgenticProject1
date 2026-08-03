"""Vision grading — grade a plan directly from its slide IMAGES via a multimodal model.

Phase 1b. The text-only grader cannot see financial tables, licenses, bank
statements, or photos (they are images), so it over-credits image-based criteria
and cannot detect problems like internally inconsistent financials. This module
renders the plan's slides to images and has a vision model (Gemini) grade them,
reusing the same rubric, guideline, calibration, and JSON parsing as the text path.

The message/prompt builders are pure and unit-tested; the live model call is
validated empirically (it needs an API key).
"""
from __future__ import annotations

import base64
from typing import List, Optional

from backend.src.grading import GradeData, parse_grader_response
from backend.src.models import RubricItem


def pngs_to_datauris(pngs: List[bytes]) -> List[str]:
    """Encode PNG bytes as base64 data URIs for an OpenAI-compatible image_url."""
    return [f"data:image/png;base64,{base64.b64encode(p).decode()}" for p in pngs]


def build_vision_user_text(rubric_str: str, guideline: str, calibration_block: str,
                           prior_feedback: str = "") -> str:
    """The text portion of the multimodal message (rubric + guideline + calibration
    + the financial-consistency emphasis + strict JSON instruction)."""
    parts: List[str] = []
    if prior_feedback:
        parts.append(prior_feedback)
    parts.append(
        "Grade this business plan STRICTLY, criterion by criterion, using the SLIDE IMAGES "
        "below. You can see everything in the slides: text, tables, charts, photos, business "
        "licenses/registration, and bank statements. Grade on what you actually see."
    )
    parts.append("RUBRIC:\n" + rubric_str)
    parts.append("JUDGES' GUIDELINE (apply throughout; may be empty):\n" + (guideline or "None provided."))
    if calibration_block:
        parts.append(calibration_block)
    parts.append(
        "FINANCIAL CHECK: read the actual numbers in any financial tables and verify they are "
        "internally consistent (profit should equal revenue minus expenses; profit cannot exceed "
        "revenue). Inconsistent or impossible figures are NOT credible — award little or no credit "
        "for the affected criteria and say so in the reason."
    )
    parts.append(
        'Return ONLY a JSON object: {"assessments":[{"criteria_index":<int>,'
        '"criteria_name":"<exact rubric name>","awarded_points":<number>,'
        '"reason":"<why, citing what you saw in the slides>"}],"general_feedback":"<summary>"}'
    )
    return "\n\n".join(parts)


def build_vision_messages(system_prompt: str, user_text: str, image_datauris: List[str]):
    """Build [SystemMessage, HumanMessage(text + images)] for a multimodal chat call."""
    from langchain_core.messages import SystemMessage, HumanMessage
    content = [{"type": "text", "text": user_text}]
    content += [{"type": "image_url", "image_url": {"url": u}} for u in image_datauris]
    return [SystemMessage(content=system_prompt), HumanMessage(content=content)]


def grade_with_vision(
    system_prompt: str,
    rubric: List[RubricItem],
    rubric_str: str,
    guideline: str,
    calibration_block: str,
    image_datauris: List[str],
    llm=None,
) -> GradeData:
    """Grade a plan from its slide images. Returns parse-safe GradeData (graded_ok
    False if there are no images or the model output is unparseable)."""
    if not image_datauris:
        return GradeData(score=0.0, graded_ok=False,
                         error="No slide images to grade (vision requires rendered pages).")
    user_text = build_vision_user_text(rubric_str, guideline, calibration_block)
    messages = build_vision_messages(system_prompt, user_text, image_datauris)
    try:
        resp = _invoke_vision(messages, llm)
    except Exception as e:
        return GradeData(score=0.0, graded_ok=False, error=f"Vision model call failed: {e}")
    return parse_grader_response(resp.content, rubric)


def _invoke_vision(messages, llm=None):
    """Call the vision model. Requests JSON mode (response_format=json_object) so
    even lighter models emit valid JSON instead of markdown-fenced/plain prose, and
    a generous max_tokens so a full-rubric response can't truncate mid-JSON. Falls
    back to a plain call if a model/endpoint rejects response_format."""
    if llm is not None:
        return llm.invoke(messages)
    from backend.src.llm import get_llm
    try:
        strict = get_llm("vision", max_tokens=8192,
                         model_kwargs={"response_format": {"type": "json_object"}})
        return strict.invoke(messages)
    except Exception:
        return get_llm("vision", max_tokens=8192).invoke(messages)
