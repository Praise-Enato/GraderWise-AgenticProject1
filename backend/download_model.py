
import os
from langchain_huggingface import HuggingFaceEmbeddings

def download_model():
    print("Starting model download...")
    print("Target: sentence-transformers/all-MiniLM-L6-v2")
    
    try:
        # This triggers the download and caching
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        print("\nSUCCESS: Model downloaded and cached successfully!")
        
        # Verify by creating a test embedding
        print("Verifying model...")
        vec = embeddings.embed_query("This is a test.")
        print(f"Verification successful. Embedding dimension: {len(vec)}")
        
    except Exception as e:
        print(f"\nERROR: Failed to download model: {e}")
        print("\nTroubleshooting:")
        print("1. Check your internet connection.")
        print("2. Ensure no firewall is blocking huggingface.co")
        print("3. Try setting proxies if you are on a corporate network.")

if __name__ == "__main__":
    download_model()
