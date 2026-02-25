import os
import sys
import logging

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from backend.src.training_data_loader import load_training_data
from backend.src.business_rag import BusinessRAG

logging.basicConfig(level=logging.INFO)

print("Loading training data with new 80-point mapped schema...")
examples = load_training_data()
print(f"Loaded {len(examples)} examples.")

print("Ingesting grading examples into Business RAG...")
count = BusinessRAG.ingest_grading_examples(examples)
print(f"Successfully ingested {count} aligned grading examples into Chroma DB.")
