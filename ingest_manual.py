import os
import sys

# Setup environment for Langchain
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
from backend.src.business_rag import BusinessRAG

def ingest():
    file_path = "backend/training_data/human_grader_instructions_summary.md"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        texts = [{
            "content": content,
            "source": "human_grader_instructions",
            "context_type": "general"  # "general" ensures it applies to all grading types
        }]
        
        count = BusinessRAG.ingest_text_documents(texts)
        print(f"Successfully ingested {count} documents into the Business RAG memory.")
    except Exception as e:
        print("Error ingesting document:", e)

if __name__ == "__main__":
    ingest()
