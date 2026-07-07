"""(Re-)ingest the static grounding corpus into its Chroma collection.

Run ONCE in an environment that has the embedding model available (after
`python backend/download_model.py`), from the repo root:

    python -m backend.scripts.ingest_reference_corpus

Idempotent: dedups by source filename, so re-running after editing a reference
doc replaces its chunks rather than duplicating them.
"""
from backend.src import reference_corpus


def main() -> None:
    docs = reference_corpus.list_reference_docs()
    print(f"Found {len(docs)} reference doc(s): {[d.split('/')[-1] for d in docs]}")
    if not docs:
        print("Nothing to ingest.")
        return
    n = reference_corpus.ingest_reference_corpus()
    print(f"Ingested {n} chunk(s) into {reference_corpus.CHROMA_REF_PATH}")
    print(f"reference_corpus_available() -> {reference_corpus.reference_corpus_available()}")


if __name__ == "__main__":
    main()
