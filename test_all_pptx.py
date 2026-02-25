import os
import sys
import pandas as pd
import asyncio
from concurrent.futures import ThreadPoolExecutor

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Add root project to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from backend.src import agent
from backend.src.pptx_processor import PPTXProcessor
from backend.src.business_rubric_templates import BYUMS_RUBRIC

files = [
    "Kachlinks Technologies.pptx",
    "Mwana Mboka Logistics.pptx",
    "Mulla Global Syatems.pptx",
    "Princess Enterprises.pptx",
    "Kalemie Mobile Outreach.pptx"
]

human_scores = {
    "Jideofor Enterprise.pptx": 36.0,
    "Princess Enterprises.pptx": 40.0,
    "Mwana Mboka Logistics.pptx": 48.0,
    "Kalemie Mobile Outreach.pptx": 60.5,
    "Kachlinks Technologies.pptx": 52.0,
    "Mulla Global Syatems.pptx": 45.0
}

async def grade_file(filename, processor):
    print(f"Began grading {filename}...")
    pptx_path = os.path.join("backend/training_data", filename)
    
    result = processor.extract_to_markdown(pptx_path)
    content = result["markdown_content"]
    
    submission_files = [{"filename": filename, "content": content}]
    
    inputs = {
        "submission_files": submission_files,
        "rubric": BYUMS_RUBRIC,
        "grading_type": "business_plan",
        "business_context_type": "byums",
        "context": [],
        "grade_result": None,
        "student_id": filename
    }
    
    try:
        loop = asyncio.get_event_loop()
        final_state = await loop.run_in_executor(None, agent.router_app.invoke, inputs)
        grade_result = final_state.get("grade_result")
        return {
            "file": filename,
            "ai_score": grade_result.score if grade_result else None,
            "error": None
        }
    except Exception as e:
        print(f"Error grading {filename}: {e}")
        return {
            "file": filename,
            "ai_score": None,
            "error": str(e)
        }

async def main():
    processor = PPTXProcessor()
    
    # We will run them sequentially to avoid rate limits
    results = []
    for filename in files:
        res = await grade_file(filename, processor)
        results.append(res)
        print(f"Finished {filename}: AI Score = {res['ai_score']}")
        
    print("\n\n" + "="*60)
    print(f"{'Business Name':<30} | {'AI Score':<10} | {'Human Score':<12}")
    print("-" * 60)
    
    for res in results:
        fname = res["file"]
        hum_score = human_scores[fname]
        ai_score = res["ai_score"]
        if ai_score is None:
            ai_score = "ERROR"
        else:
            ai_score = f"{ai_score:.1f}"
        
        name_display = fname.replace(".pptx", "")[:28]
        print(f"{name_display:<30} | {ai_score:<10} | {hum_score:<12.1f}")
        
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
