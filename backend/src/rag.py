import os
import shutil
from typing import List
from fastapi import UploadFile
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
import pandas as pd
from langchain_core.documents import Document

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from functools import lru_cache

# Constants
CHROMA_PATH = "./backend/data/chroma"
TEMP_UPLOAD_DIR = "./backend/data/temp_uploads"

# Ensure temp directory exists
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

@lru_cache(maxsize=1)
def get_embedding_function():
    try:
        return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    except Exception as e:
        print(f"Error initializing embeddings: {e}")
        raise e

def extract_text_from_file(file: UploadFile) -> str:
    """
    Extracts text from an uploaded file (PDF, DOCX, TXT, CSV, XLSX).
    For tabular data (CSV, XLSX), converts to Markdown table.
    """
    file_path = os.path.join(TEMP_UPLOAD_DIR, file.filename)
    filename_lower = file.filename.lower()
    
    # Save uploaded file temporarily
    file.file.seek(0)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    text = ""
    try:
        loader = None
        if filename_lower.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
            if loader:
                loaded_docs = loader.load()
                text = "\n".join([doc.page_content for doc in loaded_docs])
        elif filename_lower.endswith(".docx"):
            loader = Docx2txtLoader(file_path)
            if loader:
                loaded_docs = loader.load()
                text = "\n".join([doc.page_content for doc in loaded_docs])
        elif filename_lower.endswith(".txt"):
            loader = TextLoader(file_path)
            if loader:
                loaded_docs = loader.load()
                text = "\n".join([doc.page_content for doc in loaded_docs])
        elif filename_lower.endswith(".csv"):
            df = pd.read_csv(file_path)
            text = df.to_csv(index=False)
        elif filename_lower.endswith(".xlsx") or filename_lower.endswith(".xls"):
            df = pd.read_excel(file_path)
            text = df.to_csv(index=False)
        else:
            raise ValueError(f"Unsupported file type: {file.filename}")
            
    except Exception as e:
        print(f"Error loading {file.filename}: {e}")
        raise e
    finally:
        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)
            
    return text

def ingest_documents(files: List[UploadFile]) -> int:
    """
    Ingests uploaded files (PDF, DOCX, TXT, CSV, XLSX) into the vector store.
    """
    documents = []
    files_processed = 0

    for file in files:
        try:
            extracted_text = extract_text_from_file(file)
            if extracted_text:
                # Create a Document object. Metadata can be added here if needed.
                documents.append(Document(page_content=extracted_text, metadata={"source": file.filename}))
                files_processed += 1
            else:
                print(f"Warning: Extracted text was empty for {file.filename}")
        except Exception as e:
            print(f"Skipping {file.filename} due to error: {e}")

    if not documents:
        return 0

    # Split text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)

    # Embed and store in ChromaDB
    Chroma.from_documents(
        documents=splits,
        embedding=get_embedding_function(),
        persist_directory=CHROMA_PATH
    )

    return files_processed

def retrieve_context(query: str) -> List[str]:
    """
    Retrieves the top 3 relevant document chunks for the given query.
    """
    vector_store = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=get_embedding_function()
    )
    
    # Retrieve top 3
    results = vector_store.similarity_search(query, k=3)
    
    return [doc.page_content for doc in results]
