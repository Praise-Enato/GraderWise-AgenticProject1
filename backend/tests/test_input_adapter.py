"""Tests for input adapters.

Focus: YouTube-link extraction (pure), adapter routing, and the normalized
shape. PDF text/image extraction needs pypdf/PyMuPDF + a real file and is not
exercised here; those paths degrade gracefully (recorded in notes).
"""
import pytest

from backend.src.input_adapter import (
    NormalizedInput,
    PDFAdapter,
    find_youtube_url,
    get_adapter,
)


# ------------------------- youtube url extraction --------------------------- #

def test_find_youtube_watch_url():
    text = "See our pitch at https://www.youtube.com/watch?v=dQw4w9WgXcQ thanks"
    assert find_youtube_url(text) == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_find_youtube_short_url():
    assert find_youtube_url("video: https://youtu.be/dQw4w9WgXcQ") == \
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_find_youtube_embed_url():
    assert find_youtube_url("https://youtube.com/embed/dQw4w9WgXcQ") == \
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_find_youtube_no_scheme():
    assert find_youtube_url("watch at youtu.be/abc123DEF45") == \
        "https://www.youtube.com/watch?v=abc123DEF45"


def test_find_youtube_with_extra_params():
    text = "https://www.youtube.com/watch?feature=share&v=dQw4w9WgXcQ&t=30"
    assert find_youtube_url(text) == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_find_youtube_none_when_absent():
    assert find_youtube_url("no video here, just text about our business") is None


def test_find_youtube_empty():
    assert find_youtube_url("") is None


# ------------------------------ routing ------------------------------------- #

def test_get_adapter_pdf():
    assert isinstance(get_adapter("plans/entry1.pdf"), PDFAdapter)
    assert isinstance(get_adapter("ENTRY1.PDF"), PDFAdapter)


def test_get_adapter_slides_not_implemented():
    with pytest.raises(NotImplementedError):
        get_adapter("https://docs.google.com/presentation/d/abc/edit")


def test_get_adapter_unknown_raises():
    with pytest.raises(ValueError):
        get_adapter("mystery.bin")


# --------------------------- normalized shape ------------------------------- #

def test_normalized_input_flags():
    ni = NormalizedInput(text="hello", page_images=[b"png"], video_url=None)
    assert ni.has_text is True
    assert ni.has_images is True

    empty = NormalizedInput()
    assert empty.has_text is False
    assert empty.has_images is False


def test_pdf_adapter_missing_libs_degrades(tmp_path):
    # No real PDF / libs in the test env: load() must not crash; it records notes
    # and returns an empty-but-valid NormalizedInput.
    fake = tmp_path / "x.pdf"
    fake.write_bytes(b"%PDF-1.4 not really a pdf")
    ni = PDFAdapter().load(str(fake))
    assert isinstance(ni, NormalizedInput)
    assert ni.source.endswith("x.pdf")
    # either it extracted nothing (libs missing) or it read the junk; either way
    # video_url is derived from whatever text came out, and notes capture issues.
    assert ni.video_url is None
    assert isinstance(ni.notes, list)
