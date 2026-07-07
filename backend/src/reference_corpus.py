"""Grounding corpus — a small, STATIC library of generic business-plan evaluation
knowledge (financial-credibility checks, market-sizing methodology, a section-by-
section quality guide) that the grader can retrieve to ground its scoring.

Design notes:
- The corpus is GENERIC reference material authored in `backend/reference_corpus/`.
  It contains NO applicant plans and NO human scores, so grounding cannot leak
  answers the way ingesting graded plans would (contrast the old business_plan_logic
  branch, which ingested the very plans it graded). Few-shot calibration keeps its
  own leave-one-out anti-leakage path in `calibration.py`; this module is separate.
- It lives in its OWN Chroma collection (`chroma_reference`), isolated from the
  plan/academic RAG collection, with smaller chunks (concise reference docs) and
  dedup-by-source on re-ingest.
- Chroma + HuggingFace embeddings pull the heavy torch stack, so they are imported
  lazily and every retrieval degrades gracefully to [] when unavailable. Grounding
  is therefore OFF by default and purely additive: if the model/corpus aren't
  present, grading proceeds exactly as before.

Enable it by running `python -m backend.scripts.ingest_reference_corpus` (after
`backend/download_model.py`) and passing use_grounding=True.
"""
from __future__ import annotations

import os
from typing import List

REFERENCE_DIR = "./backend/reference_corpus"
CHROMA_REF_PATH = "./backend/data/chroma_reference"


def list_reference_docs() -> List[str]:
    """Absolute-ish paths of the markdown reference docs (sorted, deterministic)."""
    if not os.path.isdir(REFERENCE_DIR):
        return []
    return sorted(
        os.path.join(REFERENCE_DIR, f)
        for f in os.listdir(REFERENCE_DIR)
        if f.lower().endswith(".md")
    )


def _load_reference_documents():
    """Load each reference .md as a langchain Document tagged with its source
    filename (used for dedup-by-source and citations)."""
    from langchain_core.documents import Document  # light, but keep import local
    docs = []
    for path in list_reference_docs():
        try:
            with open(path, "r", encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            continue
        if text.strip():
            docs.append(Document(page_content=text, metadata={"source": os.path.basename(path)}))
    return docs


def ingest_reference_corpus() -> int:
    """(Re-)ingest the reference corpus into its own Chroma collection, deduping by
    source filename so re-ingesting an updated doc replaces its old chunks instead
    of duplicating them. Returns the number of chunks written. Requires the embedding
    model + chromadb; raises if they are unavailable (this is the deliberate,
    online ingestion step, not the graceful retrieval path)."""
    docs = _load_reference_documents()
    if not docs:
        return 0
    from langchain_chroma import Chroma  # lazy (pulls chromadb)
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from backend.src.rag import get_embedding_function

    vs = Chroma(persist_directory=CHROMA_REF_PATH, embedding_function=get_embedding_function())
    # Dedup-by-source: delete a filename's existing chunks before re-adding.
    for d in docs:
        src = d.metadata.get("source")
        try:
            existing = vs.get(where={"source": src})
            ids = (existing or {}).get("ids") or []
            if ids:
                vs.delete(ids=ids)
        except Exception:
            pass  # empty/new collection or backend without where-filter support
    # Smaller chunks than academic RAG — these are concise reference notes.
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    splits = splitter.split_documents(docs)
    vs.add_documents(splits)
    return len(splits)


def reference_corpus_available() -> bool:
    """Cheap check (no embeddings) for whether an ingested corpus exists on disk.
    Never raises — a permission error or TOCTOU race must degrade to 'unavailable',
    not crash the grade request that probes it (grounding is always optional)."""
    try:
        return os.path.isdir(CHROMA_REF_PATH) and bool(os.listdir(CHROMA_REF_PATH))
    except OSError:
        return False


def retrieve_reference_context(query: str, k: int = 4) -> List[str]:
    """Retrieve the top-k reference chunks for a query. Degrades gracefully to [] if
    the corpus, chromadb, or the embedding model is unavailable — grounding is a
    bonus, never a hard dependency of grading."""
    if not query or not reference_corpus_available():
        return []
    try:
        from langchain_chroma import Chroma  # lazy
        from backend.src.rag import get_embedding_function

        vs = Chroma(persist_directory=CHROMA_REF_PATH, embedding_function=get_embedding_function())
        results = vs.similarity_search(query, k=k)
        return [doc.page_content for doc in results]
    except Exception:
        return []
