import time
import sys
from sentence_transformers import SentenceTransformer

print("--- STARTING ROBUST DOWNLOAD (90MB) ---")
print("This script will keep retrying until the download finishes.")
print("Do not close this window.\n")

max_retries = 100
attempt = 0

while attempt < max_retries:
    try:
        attempt += 1
        print(f"Attempt {attempt}/{max_retries}: Downloading...")
        
        # This triggers the download
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        print("\n-----------------------------------------")
        print("✅ SUCCESS! The Brain is fully downloaded.")
        print("-----------------------------------------")
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Connection dropped. Retrying in 3 seconds...")
        time.sleep(3)

print("Failed after too many attempts. Please check your internet connection.")