import os
import glob
import logging
from typing import List
from fastapi import UploadFile
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from backend.src.rag import get_embedding_function, extract_text_from_file

logger = logging.getLogger(__name__)

# Separate ChromaDB path for business context (isolated from academic)
BUSINESS_CHROMA_PATH = "./backend/data/chroma_business"
BUSINESS_CONTEXT_DIR = "./backend/data/business_context"


class BusinessRAG:
    """
    RAG module for business plan grading context.

    Uses a separate ChromaDB collection from academic RAG, with:
    - Smaller chunk size (500 chars vs 1000) for faster, more precise retrieval
    - context_type metadata tagging for filtered queries (startup/enterprise/nonprofit)
    - Fewer retrieved chunks (5 vs 10) to keep token costs low
    """

    @staticmethod
    def _get_existing_sources() -> set:
        """Get set of already-ingested source filenames to prevent duplicates."""
        if not os.path.exists(BUSINESS_CHROMA_PATH):
            return set()
        try:
            vector_store = Chroma(
                persist_directory=BUSINESS_CHROMA_PATH,
                embedding_function=get_embedding_function()
            )
            # Get all metadata to extract unique sources
            collection = vector_store._collection
            all_metadata = collection.get(include=["metadatas"])
            sources = {m.get("source", "") for m in all_metadata.get("metadatas", []) if m}
            return sources
        except Exception as e:
            logger.warning(f"Could not check existing sources: {e}")
            return set()

    @staticmethod
    def _delete_source(filename: str):
        """Delete all documents from a specific source filename."""
        if not os.path.exists(BUSINESS_CHROMA_PATH):
            return
            
        try:
            vector_store = Chroma(
                persist_directory=BUSINESS_CHROMA_PATH,
                embedding_function=get_embedding_function()
            )
            # Delete by metadata filter
            # Note: chroma.delete might need ids, but modern versions support where filter
            # We'll try getting ids first to be safe
            collection = vector_store._collection
            result = collection.get(where={"source": filename})
            ids = result.get("ids", [])
            
            if ids:
                collection.delete(ids=ids)
                logger.info(f"Deleted {len(ids)} existing chunks for source: {filename}")
                
        except Exception as e:
            logger.error(f"Error deleting source {filename}: {e}")

    @staticmethod
    def ingest_business_context(files: List[UploadFile], context_type: str = "startup") -> int:
        """
        Ingest business context files (PDF, DOCX, TXT) into the business ChromaDB collection.
        Overwrites existing files with the same name.

        Args:
            files: List of uploaded files to ingest
            context_type: Category tag — "startup", "enterprise", "nonprofit", or "general"

        Returns:
            Number of files successfully processed
        """
        # Check existing sources to identify updates
        existing_sources = BusinessRAG._get_existing_sources()

        documents = []
        files_processed = 0
        updated = 0

        for file in files:
            # If valid overwrite, delete old version first
            if file.filename in existing_sources:
                 logger.info(f"Found existing source {file.filename}. Overwriting...")
                 BusinessRAG._delete_source(file.filename)
                 updated += 1
            
            try:
                extracted_text = extract_text_from_file(file)
                if extracted_text:
                    documents.append(Document(
                        page_content=extracted_text,
                        metadata={
                            "source": file.filename,
                            "context_type": context_type
                        }
                    ))
                    files_processed += 1
                else:
                    logger.warning(f"Extracted text was empty for {file.filename}")
            except Exception as e:
                logger.error(f"Skipping {file.filename} due to error: {e}")

        if not documents:
            return 0

        # Smaller chunks for business context — more precise retrieval
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        splits = text_splitter.split_documents(documents)

        # Store in separate business ChromaDB collection
        Chroma.from_documents(
            documents=splits,
            embedding=get_embedding_function(),
            persist_directory=BUSINESS_CHROMA_PATH
        )

        logger.info(f"Ingested {files_processed} files ({len(splits)} chunks) into business context [{context_type}]. Updated {updated} existing files.")
        return files_processed

    @staticmethod
    def ingest_text_documents(texts: List[dict]) -> int:
        """
        Ingest raw text documents (used by the starter pack auto-ingest).

        Args:
            texts: List of dicts with keys: "content", "source", "context_type"

        Returns:
            Number of documents processed
        """
        documents = []
        for item in texts:
            content = item.get("content", "")
            if content.strip():
                documents.append(Document(
                    page_content=content,
                    metadata={
                        "source": item.get("source", "unknown"),
                        "context_type": item.get("context_type", "general")
                    }
                ))

        if not documents:
            return 0

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        splits = text_splitter.split_documents(documents)

        Chroma.from_documents(
            documents=splits,
            embedding=get_embedding_function(),
            persist_directory=BUSINESS_CHROMA_PATH
        )

        logger.info(f"Ingested {len(documents)} text documents ({len(splits)} chunks) into business context")
        return len(documents)

    @staticmethod
    def retrieve_business_context(query: str, context_type: str = "startup", k: int = 5) -> List[str]:
        """
        Retrieve business context filtered by context_type.

        Args:
            query: Search query (e.g., rubric criteria text)
            context_type: Filter by context type — "startup", "enterprise", "nonprofit", "general", or "grading_examples"
            k: Number of chunks to retrieve (default 5, fewer than academic's 10)

        Returns:
            List of relevant text chunks
        """
        # Check if the business ChromaDB exists
        if not os.path.exists(BUSINESS_CHROMA_PATH):
            logger.warning("Business ChromaDB not found. No business context available.")
            return []

        try:
            vector_store = Chroma(
                persist_directory=BUSINESS_CHROMA_PATH,
                embedding_function=get_embedding_function()
            )

            # For grading_examples, only retrieve that specific type
            # For other types, also include "general" context
            if context_type == "grading_examples":
                filter_dict = {"context_type": "grading_examples"}
            else:
                filter_dict = {"context_type": {"$in": [context_type, "general"]}}

            results = vector_store.similarity_search(
                query,
                k=k,
                filter=filter_dict
            )

            return [doc.page_content for doc in results]

        except Exception as e:
            logger.error(f"Error retrieving business context: {e}")
            return []

    @staticmethod
    def ingest_grading_examples(training_examples: list) -> int:
        """
        Ingest structured grading examples from human-graded business plans
        into the business ChromaDB collection with context_type='grading_examples'.

        Each training example is split into per-category documents so similar
        past grading patterns are retrieved for the relevant rubric categories.

        Args:
            training_examples: List of dicts from training_data_loader.load_training_data()

        Returns:
            Number of documents processed
        """
        # First, delete any existing grading_examples to avoid duplicates
        BusinessRAG._delete_grading_examples()

        documents = []
        for example in training_examples:
            biz_name = example["business_name"]
            sector = example["sector"]
            grand_total = example["grand_total"]

            # Create one document per category with detailed scoring
            for category, totals in example["category_totals"].items():
                # Get the individual criteria scores for this category
                category_criteria = [
                    c for c in example["criteria_scores"]
                    if c["category"] == category
                ]

                criteria_lines = []
                for c in category_criteria:
                    criteria_lines.append(
                        f"  - {c['criteria']}: {c['awarded_points']}/{c['max_points']}"
                    )

                content = (
                    f"Human-Graded Reference — {biz_name} ({sector})\n"
                    f"Overall Score: {grand_total}/100\n"
                    f"Category: {category} — {totals['awarded']}/{totals['max']}\n"
                    f"Criteria Scores:\n" + "\n".join(criteria_lines)
                )

                documents.append(Document(
                    page_content=content,
                    metadata={
                        "source": f"training_data_{biz_name}",
                        "context_type": "grading_examples",
                        "category": category,
                        "business_name": biz_name,
                        "sector": sector,
                    }
                ))

        if not documents:
            return 0

        # Use smaller chunks since these are already concise
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        splits = text_splitter.split_documents(documents)

        Chroma.from_documents(
            documents=splits,
            embedding=get_embedding_function(),
            persist_directory=BUSINESS_CHROMA_PATH
        )

        logger.info(f"Ingested {len(documents)} grading example documents ({len(splits)} chunks)")
        return len(documents)

    @staticmethod
    def _delete_grading_examples():
        """Delete all existing grading_examples documents from ChromaDB."""
        if not os.path.exists(BUSINESS_CHROMA_PATH):
            return

        try:
            vector_store = Chroma(
                persist_directory=BUSINESS_CHROMA_PATH,
                embedding_function=get_embedding_function()
            )
            collection = vector_store._collection
            result = collection.get(where={"context_type": "grading_examples"})
            ids = result.get("ids", [])
            if ids:
                collection.delete(ids=ids)
                logger.info(f"Deleted {len(ids)} existing grading example chunks")
        except Exception as e:
            logger.warning(f"Could not delete grading examples: {e}")

    @staticmethod
    def auto_ingest_starter_pack() -> bool:
        """
        Auto-ingest starter pack files from backend/data/business_context/ on first run.

        Checks if business ChromaDB already has data. If empty, reads all .md and .txt
        files from the business_context directory and ingests them.

        Returns:
            True if starter pack was ingested, False if already populated or no files found
        """
        # Skip if business ChromaDB already has data
        existing_sources = BusinessRAG._get_existing_sources()
        if existing_sources:
            logger.info(f"Business context already has {len(existing_sources)} sources. Skipping auto-ingest.")
            return False

        # Check if starter pack directory exists
        if not os.path.exists(BUSINESS_CONTEXT_DIR):
            logger.warning(f"Starter pack directory not found: {BUSINESS_CONTEXT_DIR}")
            return False

        # Find all .md and .txt files in the starter pack directory
        starter_files = glob.glob(os.path.join(BUSINESS_CONTEXT_DIR, "*.md")) + \
                        glob.glob(os.path.join(BUSINESS_CONTEXT_DIR, "*.txt"))

        if not starter_files:
            logger.warning("No starter pack files found in business_context directory.")
            return False

        texts = []
        for file_path in starter_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                filename = os.path.basename(file_path)

                # Determine context_type from filename convention:
                # startup_*.md -> "startup", enterprise_*.md -> "enterprise", etc.
                context_type = "general"
                fname_lower = filename.lower()
                if fname_lower.startswith("startup"):
                    context_type = "startup"
                elif fname_lower.startswith("enterprise"):
                    context_type = "enterprise"
                elif fname_lower.startswith("nonprofit"):
                    context_type = "nonprofit"

                texts.append({
                    "content": content,
                    "source": filename,
                    "context_type": context_type
                })
                logger.info(f"Loaded starter file: {filename} (type: {context_type})")
            except Exception as e:
                logger.error(f"Error reading starter file {file_path}: {e}")

        if texts:
            count = BusinessRAG.ingest_text_documents(texts)
            logger.info(f"Starter pack auto-ingested: {count} files")

        # Also auto-ingest training data (grading examples) if available
        try:
            from backend.src.training_data_loader import load_training_data
            training_examples = load_training_data()
            if training_examples:
                grading_count = BusinessRAG.ingest_grading_examples(training_examples)
                logger.info(f"Auto-ingested {grading_count} grading example documents from training data")
        except Exception as e:
            logger.warning(f"Could not auto-ingest training data: {e}")

        return True
