"""/grade-vision accepts every document type an adapter can load.

Regression test for the reported bug: screening ten mixed files with Vision mode
on failed every .docx row, because the endpoint rejected anything that was not a
PDF or PPTX ("Vision grading requires a PDF or PPTX file"). A judge cannot screen
a real intake in one pass if half of it is Word documents.

The model call is stubbed — this is about what the endpoint accepts and what
evidence it assembles, not about grading quality.
"""
import io
import json
import zipfile

import pytest
from fastapi.testclient import TestClient

import backend.src.main as main
from backend.src import persistence as P
from backend.src.grading import GradeData
from backend.src.models import CriterionAssessment
from backend.src.main import app, get_session

RUBRIC = json.dumps([{"criteria": "Financials - Detail", "max_points": 5,
                      "description": "detail"}])


@pytest.fixture()
def client(tmp_path, monkeypatch):
    engine = P.make_engine(f"sqlite:///{tmp_path/'vision.db'}")
    P.init_db(engine)
    Factory = P.make_session_factory(engine)

    def _override():
        s = Factory()
        try:
            yield s
        finally:
            s.close()

    # Capture what evidence the endpoint handed the grader, and never call a model.
    seen = {}

    def fake_grade_with_vision(system_prompt, rubric_items, rubric_str, guideline,
                               calib, image_uris, submission_text="", **kw):
        seen["images"] = len(image_uris)
        seen["text"] = submission_text
        return GradeData(score=3.0, graded_ok=True, general_feedback="ok", assessments=[
            CriterionAssessment(criteria_index=1, criteria_name="Financials - Detail",
                                awarded_points=3.0, max_points=5.0, reason="partial")])

    monkeypatch.setattr(main.vision_grade, "grade_with_vision", fake_grade_with_vision)
    monkeypatch.setattr(main.agent, "_load_fewshot_examples", lambda: [])

    app.dependency_overrides[get_session] = _override
    yield TestClient(app), seen
    app.dependency_overrides.clear()


# --------------------------- fixtures on disk ------------------------------- #

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _docx_bytes(paragraphs=("Acme Ventures", "Revenue $50,000"), images=()):
    body = "".join(
        f'<w:p><w:r><w:t xml:space="preserve">{p}</w:t></w:r></w:p>' for p in paragraphs)
    doc = (f'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="{_W}">'
           f"<w:body>{body}</w:body></w:document>")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.'
                   'openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Default Extension="png" ContentType="image/png"/></Types>')
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://'
                   'schemas.openxmlformats.org/package/2006/relationships"/>')
        z.writestr("word/document.xml", doc)
        for i, blob in enumerate(images, 1):
            z.writestr(f"word/media/image{i}.png", blob)
    return buf.getvalue()


def _png():
    Image = pytest.importorskip("PIL.Image", reason="Pillow not installed")
    b = io.BytesIO()
    Image.new("RGB", (8, 8), (7, 7, 7)).save(b, format="PNG")
    return b.getvalue()


def _post(tc, filename, content, ctype="application/octet-stream"):
    return tc.post("/grade-vision",
                   files={"files": (filename, content, ctype)},
                   data={"rubric": RUBRIC, "guideline": "", "student_id": "team",
                         "use_calibration": "false"})


# --------------------------- the regression --------------------------------- #

def test_docx_is_graded_from_its_text(client):
    tc, seen = client
    r = _post(tc, "plan.docx", _docx_bytes())
    assert r.status_code == 200, r.text
    assert r.json()["score"] == 3.0
    # No pictures in this .docx, so text is the whole of the evidence.
    assert seen["images"] == 0
    assert "Acme Ventures" in seen["text"] and "$50,000" in seen["text"]


def test_docx_embedded_pictures_reach_the_model(client):
    tc, seen = client
    r = _post(tc, "plan.docx", _docx_bytes(images=[_png(), _png()]))
    assert r.status_code == 200, r.text
    assert seen["images"] == 2          # licence/bank scans are the point
    assert "Acme Ventures" in seen["text"]


@pytest.mark.parametrize("name", ["plan.txt", "plan.md"])
def test_plain_text_and_markdown_are_graded(client, name):
    tc, seen = client
    r = _post(tc, name, b"# Acme Ventures\n\nRevenue $50,000 in year one.\n", "text/plain")
    assert r.status_code == 200, r.text
    assert seen["images"] == 0
    assert "Acme Ventures" in seen["text"]


def test_unsupported_type_is_still_rejected(client):
    tc, _ = client
    r = _post(tc, "plan.xlsx", b"PK\x03\x04not-a-plan")
    assert r.status_code == 422
    assert "Supported" in r.json()["detail"]


def test_a_file_with_neither_text_nor_images_is_rejected(client):
    tc, _ = client
    r = _post(tc, "plan.txt", b"   \n\t\n ", "text/plain")
    assert r.status_code == 422
    assert "nothing to grade" in r.json()["detail"].lower()


def test_the_log_says_it_was_graded_from_text(client):
    tc, _ = client
    body = _post(tc, "plan.docx", _docx_bytes()).json()
    log = " ".join(body["thinking_process"]).lower()
    assert "no images" in log and "extracted text" in log


def test_history_records_the_docx_run(client):
    tc, _ = client
    assert _post(tc, "plan.docx", _docx_bytes()).status_code == 200
    rows = tc.get("/grade-history").json()
    assert any(r["filename"] == "plan.docx" for r in rows)
