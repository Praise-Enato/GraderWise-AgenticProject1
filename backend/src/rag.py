import os
import shutil
from typing import List
from fastapi import UploadFile
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Constants
CHROMA_PATH = "./backend/data/chroma"
TEMP_UPLOAD_DIR = "./backend/data/temp_uploads"

# Ensure temp directory exists
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

# Initialize Embeddings
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def ingest_course_material(files: List[UploadFile]) -> int:
    """
    Ingests uploaded PDF files into the vector store.
    """
    documents = []
    files_processed = 0

    for file in files:
        file_path = os.path.join(TEMP_UPLOAD_DIR, file.filename)
        
        # Save uploaded file temporarily
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        try:
            # Load PDF
            loader = PyPDFLoader(file_path)
            loaded_docs = loader.load()
            documents.extend(loaded_docs)
            files_processed += 1
        finally:
            # Clean up temp file
            if os.path.exists(file_path):
                os.remove(file_path)

    if not documents:
        return 0

    # Split text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)

    # Embed and store in ChromaDB
    # Persist directory is handled automatically by langchain_chroma.Chroma in newer versions
    # or requires explicit client settings, but basic usage here typically implies persistence if directory provided.
    # Note: langchain-chroma 0.1.0+ uses persistent_client automatically if persist_directory is passed?
    # Providing persist_directory to Chroma constructor.
    
    Chroma.from_documents(
        documents=splits,
        embedding=embedding_function,
        persist_directory=CHROMA_PATH
    )

    return files_processed

def retrieve_context(query: str) -> List[str]:
    """
    Retrieves the top 3 relevant document chunks for the given query.
    """
    vector_store = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embedding_function
    )
    
    # Retrieve top 3
    results = vector_store.similarity_search(query, k=3)
    
    return [doc.page_content for doc in results]
