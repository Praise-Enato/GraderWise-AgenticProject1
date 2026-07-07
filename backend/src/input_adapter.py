"""Input adapters — normalize any submission source to a common shape.

The submission source will change (PDF for the demo; possibly a Google Slides
link later). To avoid painting the pipeline into a corner, everything goes
through an adapter that yields a NormalizedInput{ text, page_images, video_url }.
Swapping PDF -> Slides later is a new adapter, not a pipeline rewrite (same idea
as the model router).

For the demo only the PDF adapter is built. The pure parts (YouTube-link
extraction, adapter routing, the normalized shape) are unit-tested; PDF text and
page-image extraction lazily import pypdf / PyMuPDF and degrade gracefully when
those libraries are absent.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class NormalizedInput:
    text: str = ""
    page_images: List[bytes] = field(default_factory=list)  # PNG bytes per page (for vision model)
    video_url: Optional[str] = None
    source: str = ""
    notes: List[str] = field(default_factory=list)  # non-fatal issues (e.g. image render unavailable)

    @property
    def has_text(self) -> bool:
        return bool(self.text and self.text.strip())

    @property
    def has_images(self) -> bool:
        return len(self.page_images) > 0


# youtube.com/watch?v=ID, youtu.be/ID, youtube.com/embed/ID, /shorts/ID, /live/ID
_YT_RE = re.compile(
    r"(?:https?://)?(?:www\.)?"
    r"(?:youtube\.com/(?:watch\?(?:[^ \n]*&)?v=|embed/|shorts/|live/)|youtu\.be/)"
    r"([A-Za-z0-9_-]{11})",
    re.IGNORECASE,
)


def find_youtube_url(text: str) -> Optional[str]:
    """Return the first YouTube video URL found in text, normalized to a canonical
    watch URL, or None. The video link is embedded in the slide deck per the
    competition handbook, so this is how Phase 1b gets the video to grade."""
    if not text:
        return None
    m = _YT_RE.search(text)
    if not m:
        return None
    return f"https://www.youtube.com/watch?v={m.group(1)}"


class InputAdapter:
    """Interface: load(source) -> NormalizedInput."""

    def load(self, source: str) -> NormalizedInput:  # pragma: no cover - interface
        raise NotImplementedError


class PDFAdapter(InputAdapter):
    """Load a submission from a PDF (typically a slide deck exported to PDF)."""

    def load(self, source: str) -> NormalizedInput:
        result = NormalizedInput(source=source)
        result.text = self._extract_text(source, result.notes)
        result.video_url = find_youtube_url(result.text)
        result.page_images = self._render_pages(source, result.notes)
        return result

    @staticmethod
    def _extract_text(path: str, notes: List[str]) -> str:
        try:
            import pypdf  # lazy: heavy optional dep
        except ImportError:
            notes.append("pypdf not installed — no text extracted.")
            return ""
        try:
            reader = pypdf.PdfReader(path)
            parts = []
            for page in reader.pages:
                try:
                    parts.append(page.extract_text() or "")
                except Exception as e:  # pragma: no cover - per-page defensive
                    notes.append(f"page text extraction error: {e}")
            return "\n".join(p for p in parts if p)
        except Exception as e:
            notes.append(f"PDF read error: {e}")
            return ""

    @staticmethod
    def _render_pages(path: str, notes: List[str], dpi: int = 130, max_pages: int = 30) -> List[bytes]:
        """Render each PDF page to PNG bytes for the vision model. Slide-deck PDFs
        carry the financials/license/bank/photos as images, so text alone is not
        enough (eng review). Uses PyMuPDF if available. Capped at max_pages to bound
        the multimodal payload size."""
        try:
            import fitz  # PyMuPDF, lazy optional dep
        except ImportError:
            notes.append("PyMuPDF (fitz) not installed — page images unavailable; "
                         "vision grading will have no slide images.")
            return []
        try:
            doc = fitz.open(path)
            images = []
            for i, page in enumerate(doc):
                if i >= max_pages:
                    notes.append(f"PDF has {doc.page_count} pages; rendered first {max_pages} for vision.")
                    break
                images.append(page.get_pixmap(dpi=dpi).tobytes("png"))
            return images
        except Exception as e:  # pragma: no cover - defensive
            notes.append(f"page render error: {e}")
            return []


def render_pdf_images(path: str, dpi: int = 130, max_pages: int = 30) -> List[bytes]:
    """Render a PDF's pages to PNG bytes (for vision grading). Returns [] if
    PyMuPDF is unavailable. Capped at max_pages to bound payload size."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return []
    images: List[bytes] = []
    doc = fitz.open(path)
    for i, page in enumerate(doc):
        if i >= max_pages:
            break
        images.append(page.get_pixmap(dpi=dpi).tobytes("png"))
    return images


def get_adapter(source: str) -> InputAdapter:
    """Select an adapter for a submission source. Only PDF for the demo; the
    Google Slides path is a deliberate, clearly-signposted extension point."""
    s = source.lower()
    if s.endswith(".pdf"):
        return PDFAdapter()
    if "docs.google.com/presentation" in s or "slides.google.com" in s:
        raise NotImplementedError(
            "Google Slides adapter is future work; only PDF is supported for the demo."
        )
    raise ValueError(f"No input adapter for source: {source}")
