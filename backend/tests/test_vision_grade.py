"""Tests for vision grading (pure builders + orchestration with a fake model)."""
import base64
import json

from backend.src import vision_grade as VG
from backend.src.models import RubricItem


def rubric():
    return [RubricItem(criteria="Financials - Detailed Breakdown", max_points=5, description="detail")]


# ------------------------------ data URIs ----------------------------------- #

def test_pngs_to_datauris():
    uris = VG.pngs_to_datauris([b"\x89PNG-fake", b"other"])
    assert uris[0].startswith("data:image/png;base64,")
    # decodes back to the original bytes
    assert base64.b64decode(uris[0].split(",", 1)[1]) == b"\x89PNG-fake"
    assert len(uris) == 2


# ------------------------------ user text ----------------------------------- #

def test_user_text_has_rubric_guideline_financial_check_and_json():
    txt = VG.build_vision_user_text("RUBRIC_STR", "GUIDE", "CALIB_BLOCK")
    assert "RUBRIC_STR" in txt
    assert "GUIDE" in txt
    assert "CALIB_BLOCK" in txt
    assert "FINANCIAL CHECK" in txt
    assert "profit cannot exceed" in txt
    assert '"assessments"' in txt  # strict JSON instruction


def test_user_text_prepends_prior_feedback():
    txt = VG.build_vision_user_text("R", "G", "", prior_feedback="FIX THIS.")
    assert txt.startswith("FIX THIS.")


def test_user_text_handles_empty_guideline_and_calibration():
    txt = VG.build_vision_user_text("R", "", "")
    assert "None provided." in txt  # empty guideline
    assert "CALIBRATION" not in txt  # no calibration block appended when empty


# ---------------------------- messages -------------------------------------- #

def test_build_messages_structure():
    msgs = VG.build_vision_messages("SYS", "USER", ["data:image/png;base64,AAA", "data:image/png;base64,BBB"])
    assert len(msgs) == 2
    assert msgs[0].content == "SYS"
    content = msgs[1].content
    # one text part + two image parts
    assert content[0] == {"type": "text", "text": "USER"}
    imgs = [c for c in content if c.get("type") == "image_url"]
    assert len(imgs) == 2
    assert imgs[0]["image_url"]["url"].startswith("data:image/png;base64,")


# --------------------------- grade_with_vision ------------------------------ #

class _FakeLLM:
    def __init__(self, content):
        self._content = content
    def invoke(self, messages):
        class R:
            content = self._content
        # capture that images were passed
        self.last = messages
        return R()


def test_grade_with_vision_parses_model_json():
    payload = json.dumps({"assessments": [
        {"criteria_index": 1, "criteria_name": "Financials - Detailed Breakdown",
         "awarded_points": 1, "reason": "numbers inconsistent"}],
        "general_feedback": "thin financials"})
    gd = VG.grade_with_vision("SYS", rubric(), "RSTR", "G", "", ["data:image/png;base64,AAA"],
                              llm=_FakeLLM(payload))
    assert gd.graded_ok is True
    assert gd.score == 1.0
    assert gd.general_feedback == "thin financials"
    assert gd.assessments[0].reason == "numbers inconsistent"


def test_grade_with_vision_grades_text_only_documents():
    # No images is NOT a refusal any more: a .docx without pictures, a .txt or a
    # .md has nothing to render, and refusing it meant a mixed batch (some PDFs,
    # some DOCX) could not be screened in one Vision pass.
    payload = json.dumps({"assessments": [
        {"criteria_index": 1, "criteria_name": "Financials - Detailed Breakdown",
         "awarded_points": 2, "reason": "no projections in the text"}],
        "general_feedback": "add unit economics"})
    gd = VG.grade_with_vision("SYS", rubric(), "RSTR", "G", "", [],
                              llm=_FakeLLM(payload),
                              submission_text="Acme Ventures. Revenue $50,000.")
    assert gd.graded_ok is True
    assert gd.score == 2.0
    assert gd.general_feedback == "add unit economics"


def test_grade_with_vision_needs_text_or_images():
    # Only a file that yielded nothing at all is refused.
    gd = VG.grade_with_vision("SYS", rubric(), "RSTR", "G", "", [], llm=_FakeLLM("{}"))
    assert gd.graded_ok is False
    assert "Nothing to grade" in gd.error

    blank = VG.grade_with_vision("SYS", rubric(), "RSTR", "G", "", [], llm=_FakeLLM("{}"),
                                 submission_text="   \n\t ")
    assert blank.graded_ok is False


def test_text_only_prompt_does_not_ask_the_model_to_read_images():
    # Telling a model to read slides that do not exist invites it to invent them.
    txt = VG.build_vision_user_text("RSTR", "G", "", submission_text="body",
                                    has_images=False)
    assert "DOCUMENT TEXT" in txt
    assert "SLIDE IMAGES" not in txt
    assert "no images to read" in txt
    assert "FINANCIAL CHECK" in txt          # still graded strictly on the numbers

    withimg = VG.build_vision_user_text("RSTR", "G", "", submission_text="body",
                                        has_images=True)
    assert "SLIDE IMAGES" in withimg
    assert "SLIDE TEXT" in withimg


def test_messages_carry_only_text_when_there_are_no_images():
    msgs = VG.build_vision_messages("SYS", "USER_TEXT", [])
    content = msgs[1].content
    assert len(content) == 1
    assert content[0]["type"] == "text"


def test_grade_with_vision_model_error_flagged():
    class Boom:
        def invoke(self, m):
            raise RuntimeError("api down")
    gd = VG.grade_with_vision("SYS", rubric(), "RSTR", "G", "", ["data:image/png;base64,AAA"], llm=Boom())
    assert gd.graded_ok is False
    assert "Vision model call failed" in gd.error


def test_grade_with_vision_unparseable_flagged():
    gd = VG.grade_with_vision("SYS", rubric(), "RSTR", "G", "", ["data:image/png;base64,AAA"],
                              llm=_FakeLLM("not json"))
    assert gd.graded_ok is False


# --------------------------- ensemble (vision path) ------------------------- #
# The vision path graded ONCE, so PDF/PPTX — the formats entrants are told to
# prefer — had no defence against the grader disagreeing with itself (measured
# sd ~2.9, 16.5-point range over 40 identical runs of one plan).

class _SeqLLM:
    """Returns a different score per call, so aggregation is observable."""
    def __init__(self, scores):
        self._scores = list(scores)
        self.calls = 0
        self.temperatures = []
    def invoke(self, messages):
        s = self._scores[self.calls % len(self._scores)]
        self.calls += 1
        class R:
            content = json.dumps({"assessments": [
                {"criteria_index": 1, "criteria_name": "Financials - Detailed Breakdown",
                 "awarded_points": s, "max_points": 5}], "general_feedback": "f"})
        return R()


def test_ensemble_takes_the_per_criterion_median():
    llm = _SeqLLM([1, 5, 2])          # median 2, NOT the mean (2.67) or the outlier 5
    gd = VG.grade_with_vision_ensemble("SYS", rubric(), "RSTR", "G", "",
                                       ["data:image/png;base64,AAA"], llm=llm,
                                       submission_text="body", ensemble_n=3)
    assert llm.calls == 3
    assert gd.graded_ok is True
    assert gd.score == 2.0


def test_ensemble_n_1_is_a_single_unchanged_pass():
    llm = _SeqLLM([3])
    gd = VG.grade_with_vision_ensemble("SYS", rubric(), "RSTR", "G", "",
                                       ["data:image/png;base64,AAA"], llm=llm,
                                       submission_text="body", ensemble_n=1)
    assert llm.calls == 1
    assert gd.score == 3.0


def test_ensemble_defaults_are_shared_with_the_text_path():
    # One constant, so the two paths cannot drift apart.
    from backend.src.grading import DEFAULT_ENSEMBLE_N, DEFAULT_ENSEMBLE_TEMPERATURE
    assert DEFAULT_ENSEMBLE_N == 3
    # ZERO on purpose: 0.4 measurably wasted the median's benefit (median-of-3 at
    # 0.4 was barely tighter than a single pass at 0.0). Changing this needs a
    # re-measurement, not a preference.
    assert DEFAULT_ENSEMBLE_TEMPERATURE == 0.0


def test_explicit_zero_temperature_is_not_coerced_to_a_fallback():
    # `x or default` silently turns 0.0 into the default; this pins that it doesn't.
    import inspect
    src = inspect.getsource(VG.grade_with_vision_ensemble)
    assert "ensemble_temperature or" not in src
