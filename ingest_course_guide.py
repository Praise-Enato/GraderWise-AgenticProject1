import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from langchain_chroma import Chroma
from langchain_text_splitters import MarkdownHeaderTextSplitter
from backend.src.rag import get_embedding_function

# Paths
BUSINESS_CHROMA_PATH = "./backend/data/chroma_business"
GUIDE_PATH = "backend/training_data/course_guide.md"

def main():
    if not os.path.exists(GUIDE_PATH):
        print("Course guide not found.")
        return

    with open(GUIDE_PATH, "r", encoding="utf-8") as f:
        markdown_document = f.read()

    headers_to_split_on = [
        ("##", "Header 2")
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    md_header_splits = markdown_splitter.split_text(markdown_document)

    # Add metadata to each chunk
    for split in md_header_splits:
        split.metadata["source"] = "course_guide.md"
        split.metadata["context_type"] = "general"

    print(f"Split course guide into {len(md_header_splits)} header-based chunks.")

    Chroma.from_documents(
        documents=md_header_splits,
        embedding=get_embedding_function(),
        persist_directory=BUSINESS_CHROMA_PATH
    )
    
    print("Sucessfully ingested course guide into BusinessRAG.")

if __name__ == "__main__":
    main()
