
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

print("--- DIAGNOSTIC SCRIPT START ---")

# 1. Load .env
load_dotenv()
key = os.getenv("DEEPSEEK_API_KEY")
print(f"1. Env Key Found: {bool(key)}")
if key:
    print(f"   Key Prefix: {key[:4]}...")
    print(f"   Key Length: {len(key)}")

# 2. Initialize LLM
try:
    print("2. Initializing ChatOpenAI...")
    llm = ChatOpenAI(
        model="deepseek-chat",
        openai_api_key=key,
        openai_api_base="https://api.deepseek.com",
        temperature=0
    )
    print("   Initialization Success.")
    
    # 3. Test Invoke
    print("3. Testing Invoke...")
    res = llm.invoke("Hello")
    print(f"   Invoke Result: {res.content}")
    print("✅ SUCCESS: Backend logic should work.")

except Exception as e:
    print(f"❌ ERROR: {e}")

print("--- DIAGNOSTIC SCRIPT END ---")
