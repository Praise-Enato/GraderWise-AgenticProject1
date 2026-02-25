import os
import sys
import asyncio
import pandas as pd
from pprint import pprint

# Set environment variables for LangChain/HuggingFace to avoid issues
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Add root project to sys.path so backend imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from backend.src import agent
from backend.src.pptx_processor import PPTXProcessor
from backend.src.business_rubric_templates import BYUMS_RUBRIC

async def test_single():
    print("Testing single PPTX file...")
    processor = PPTXProcessor()
    pptx_path = "backend/training_data/Kachlinks Technologies.pptx"
    
    print(f"Extracting markdown from {pptx_path}")
    result = processor.extract_to_markdown(pptx_path)
    content = result["markdown_content"]
    
    submission_files = [{"filename": "Kachlinks Technologies.pptx", "content": content}]
    
    inputs = {
        "submission_files": submission_files,
        "rubric": BYUMS_RUBRIC,
        "grading_type": "business_plan",
        "business_context_type": "byums",
        "context": [],
        "grade_result": None,
        "student_id": "test_student"
    }
    
    print("Invoking grader...")
    # router_app.invoke is synchronous in langchain if not ainvoked
    try:
        final_state = agent.router_app.invoke(inputs)
        grade_result = final_state.get("grade_result")
        print("\n=== GRADING COMPLETE ===")
        print(f"Total Score: {grade_result.total_score}")
        print("Feedback excerpt:")
        print(grade_result.overall_feedback[:500])
    except Exception as e:
        print("Error invoking router_app:", e)

if __name__ == "__main__":
    asyncio.run(test_single())
