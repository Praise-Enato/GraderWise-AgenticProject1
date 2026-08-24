"""Tests for Word (.docx) and plain-text (.txt/.md) submission support.

These types exist so that Vision mode can screen a MIXED batch in one pass. Before
this, selecting Vision with ten files where some were .docx failed every .docx row
with a 422 — the vision path required a PDF or PPTX.

.docx files are authored here as minimal OOXML zips rather than with python-docx,
which is deliberately not a dependency (docx2txt already reads .docx for the text
path, and a .docx's pictures come out of its zip with the stdlib). The zip is real
enough for docx2txt: verified to yield both paragraph text and table cells.
"""
import io
import zipfile

import pytest

from backend.src import input_adapter as IA
from backend.src.input_adapter import (
    ADAPTER_SUFFIXES,
    DOCXAdapter,
    NormalizedInput,
    TextAdapter,
    get_adapter,
)

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Default Extension="png" ContentType="image/png"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-'
    'officedocument.wordprocessingml.document.main+xml"/></Types>'
)
_RELS = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
    'relationships/officeDocument" Target="word/document.xml"/></Relationships>'
)


def _png(colour=(10, 20, 30), size=(8, 8)) -> bytes:
    Image = pytest.importorskip("PIL.Image", reason="Pillow not installed")
    buf = io.BytesIO()
    Image.new("RGB", size, colour).save(buf, format="PNG")
    return buf.getvalue()


def _docx(path, paragraphs=(), table_rows=(), images=(), include_media_dir=False):
    """Author a minimal but real .docx at `path`."""
    def para(t):
        return f'<w:p><w:r><w:t xml:space="preserve">{t}</w:t></w:r></w:p>'

    body = "".join(para(p) for p in paragraphs)
    if table_rows:
        rows = "".join(
            "<w:tr>" + "".join(f"<w:tc>{para(c)}</w:tc>" for c in row) + "</w:tr>"
            for row in table_rows
        )
        body += f"<w:tbl>{rows}</w:tbl>"
    doc = (f'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="{_W}">'
           f"<w:body>{body}</w:body></w:document>")
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", _CONTENT_TYPES)
        z.writestr("_rels/.rels", _RELS)
        z.writestr("word/document.xml", doc)
        if include_media_dir:
            z.writestr("word/media/", b"")      # a real docx carries this entry
        for i, blob in enumerate(images, 1):
            z.writestr(f"word/media/image{i}.png", blob)
    return str(path)


# --------------------------- adapter routing -------------------------------- #

@pytest.mark.parametrize("name,cls", [
    ("plan.docx", DOCXAdapter), ("PLAN.DOCX", DOCXAdapter),
    ("plan.txt", TextAdapter), ("plan.md", TextAdapter),
    ("plan.markdown", TextAdapter), ("PLAN.MD", TextAdapter),
])
def test_get_adapter_routes_the_new_types(name, cls):
    assert isinstance(get_adapter(name), cls)


def test_get_adapter_still_rejects_genuinely_unsupported():
    with pytest.raises(ValueError):
        get_adapter("plan.xlsx")


def test_adapter_suffixes_covers_every_routed_type():
    # The API's upload check and the frontend pickers are driven off this tuple,
    # so anything get_adapter handles has to be in it.
    for suffix in (".pdf", ".pptx", ".docx", ".txt", ".md", ".markdown"):
        assert suffix in ADAPTER_SUFFIXES
        assert get_adapter(f"plan{suffix}") is not None


# --------------------------- .docx text ------------------------------------- #

def test_docx_text_includes_paragraphs_and_table_cells(tmp_path):
    # Financials live in tables; the whole point of reading them is the numbers.
    path = _docx(tmp_path / "p.docx",
                 paragraphs=["FrostFlow Ice Ventures", "Executive Summary"],
                 table_rows=[["Revenue", "$50,000"], ["Profit", "$12,000"]])
    text = IA.extract_docx_text(path)
    assert "FrostFlow Ice Ventures" in text
    assert "Revenue" in text and "$50,000" in text
    assert "Profit" in text and "$12,000" in text


def test_docx_adapter_yields_text_and_finds_the_video_link(tmp_path):
    path = _docx(tmp_path / "p.docx", paragraphs=[
        "Acme Ventures", "Watch: https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    ])
    ni = DOCXAdapter().load(path)
    assert isinstance(ni, NormalizedInput)
    assert ni.has_text
    assert ni.video_url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_docx_unreadable_file_degrades_without_raising(tmp_path):
    bad = tmp_path / "broken.docx"
    bad.write_bytes(b"this is not a zip")
    ni = DOCXAdapter().load(str(bad))
    assert ni.text == ""
    assert ni.page_images == []
    assert ni.notes  # the failure is recorded, not swallowed silently


# --------------------------- .docx images ----------------------------------- #

def test_docx_embedded_images_are_extracted(tmp_path):
    # One real corpus plan carries three JPEGs — the licence/bank evidence the
    # vision path exists to read.
    path = _docx(tmp_path / "p.docx", paragraphs=["Acme"],
                 images=[_png((1, 2, 3)), _png((4, 5, 6))], include_media_dir=True)
    images = IA.extract_docx_images(path)
    assert len(images) == 2                       # the media/ dir entry is skipped
    assert all(b[:8] == b"\x89PNG\r\n\x1a\n" for b in images)


def test_docx_without_pictures_yields_no_images_but_still_has_text(tmp_path):
    # The common case for a prose plan — and it must still be gradeable.
    path = _docx(tmp_path / "p.docx", paragraphs=["Acme Ventures", "We sell ice."])
    ni = DOCXAdapter().load(path)
    assert ni.page_images == []
    assert ni.has_text is True


def test_docx_image_cap_is_honoured(tmp_path):
    path = _docx(tmp_path / "p.docx", paragraphs=["Acme"], images=[_png() for _ in range(5)])
    assert len(IA.extract_docx_images(path, max_images=3)) == 3


# --------------------------- .txt / .md ------------------------------------- #

def test_text_adapter_reads_utf8(tmp_path):
    p = tmp_path / "plan.md"
    p.write_text("# Acme Ventures\n\nWe sell ice in Kakata.\n", encoding="utf-8")
    ni = TextAdapter().load(str(p))
    assert "Acme Ventures" in ni.text
    assert ni.page_images == []          # nothing to render, by definition
    assert ni.has_images is False


def test_text_adapter_handles_bom_and_cp1252(tmp_path):
    bom = tmp_path / "a.txt"
    bom.write_bytes("﻿Acme Ventures".encode("utf-8"))
    assert IA.extract_plain_text(str(bom)) == "Acme Ventures"

    # A judge's upload can be cp1252; losing the plan would be worse than losing
    # a character, so decoding is permissive.
    cp = tmp_path / "b.txt"
    cp.write_bytes("Café Zoë Ventures".encode("cp1252"))
    got = IA.extract_plain_text(str(cp))
    assert "Ventures" in got and got != ""


def test_text_adapter_finds_the_video_link(tmp_path):
    p = tmp_path / "plan.txt"
    p.write_text("Acme\nhttps://youtu.be/dQw4w9WgXcQ\n")
    assert TextAdapter().load(str(p)).video_url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_empty_text_file_is_noted(tmp_path):
    p = tmp_path / "plan.txt"
    p.write_text("   \n\n")
    ni = TextAdapter().load(str(p))
    assert ni.text == ""
    assert ni.has_text is False
    assert ni.notes


def test_missing_text_file_degrades(tmp_path):
    ni = TextAdapter().load(str(tmp_path / "nope.txt"))
    assert ni.text == ""
    assert ni.notes
