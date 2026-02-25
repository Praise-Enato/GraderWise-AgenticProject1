"""
Ingest Training Data — Loads human-graded business plan examples
into the ChromaDB business context collection for RAG retrieval.

Run this script once (or re-run to refresh) to populate the database
with grading examples from the BYUMS rubric spreadsheet.

Usage:
    cd /path/to/GraderWise-AgenticProject1
    source praise.venv/bin/activate
    python -m backend.scripts.ingest_training_data
"""

import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    logger.info("Loading training data from BYUMS rubric spreadsheet...")

    from backend.src.training_data_loader import load_training_data
    from backend.src.business_rag import BusinessRAG

    # Load the training examples
    examples = load_training_data()

    if not examples:
        logger.error("No training examples loaded. Check the spreadsheet path.")
        sys.exit(1)

    logger.info(f"Loaded {len(examples)} training examples:")
    for ex in examples:
        text_info = f", {len(ex['pptx_text'])} chars of text" if ex['pptx_text'] else ", no text (image-based)"
        logger.info(f"  • {ex['business_name']} ({ex['sector']}) — {ex['grand_total']}/100{text_info}")

    # Ingest into ChromaDB as grading_examples
    logger.info("\nIngesting grading examples into ChromaDB...")
    count = BusinessRAG.ingest_grading_examples(examples)
    logger.info(f"Successfully ingested {count} grading example documents into ChromaDB")

    # Verify retrieval works
    logger.info("\nVerifying retrieval...")
    test_queries = [
        "financial projections and revenue forecast",
        "marketing strategy and customer acquisition",
        "management team expertise and leadership",
    ]
    for query in test_queries:
        results = BusinessRAG.retrieve_business_context(
            query=query, context_type="grading_examples", k=2
        )
        logger.info(f"\n  Query: '{query}'")
        for i, r in enumerate(results):
            logger.info(f"  Result {i+1}: {r[:120]}...")

    logger.info("\n✅ Training data ingestion complete!")


if __name__ == "__main__":
    main()
