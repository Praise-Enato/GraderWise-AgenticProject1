"""
Test script for LangGraph orchestration logic.
This script verifies the grading workflow with dummy data and mocked RAG retrieval.
"""

import sys
import os
# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import patch
from backend.src.models import RubricItem, GradeResult
from backend.src import agent

# Dummy test data
DUMMY_RUBRIC = [
    RubricItem(
        criteria="Content Quality",
        max_points=30,
        description="Demonstrates deep understanding of the topic with accurate information and comprehensive coverage"
    ),
    RubricItem(
        criteria="Technical Accuracy",
        max_points=40,
        description="All technical details, code examples, and explanations are correct and follow best practices"
    ),
    RubricItem(
        criteria="Clarity and Organization",
        max_points=30,
        description="Ideas are presented clearly with logical flow and proper structure"
    )
]

DUMMY_SUBMISSION = """
Python is a high-level programming language that supports multiple programming paradigms including 
object-oriented, functional, and procedural programming. It uses dynamic typing and automatic memory 
management through garbage collection.

Key features include:
1. Simple and readable syntax that emphasizes code readability
2. Extensive standard library with built-in modules for various tasks
3. Strong community support and vast ecosystem of third-party packages via PyPI

Python is widely used in web development (Django, Flask), data science (NumPy, Pandas), 
machine learning (TensorFlow, PyTorch), and automation scripting.
"""

DUMMY_CONTEXT = [
    "Python is an interpreted, high-level programming language created by Guido van Rossum in 1991. "
    "It emphasizes code readability with significant whitespace and supports multiple programming paradigms.",
    
    "Python's standard library is extensive and includes modules for file I/O, system calls, networking, "
    "and even Internet protocols. The language also supports dynamic typing and automatic memory management.",
    
    "Popular Python frameworks include Django and Flask for web development, NumPy and Pandas for data analysis, "
    "and TensorFlow and PyTorch for machine learning applications."
]


def mock_retrieve_context(query: str):
    """Mock function to replace rag.retrieve_context"""
    print(f"[MOCK] Retrieving context for query: {query[:50]}...")
    return DUMMY_CONTEXT


def main():
    print("=" * 80)
    print("LANGGRAPH ORCHESTRATION TEST")
    print("=" * 80)
    print()
    
    # Mock the RAG retrieval function
    with patch('backend.src.rag.retrieve_context', side_effect=mock_retrieve_context):
        print("[*] Test Configuration:")
        print(f"   - Rubric Items: {len(DUMMY_RUBRIC)}")
        print(f"   - Max Possible Score: {sum(item.max_points for item in DUMMY_RUBRIC)}")
        print(f"   - Submission Length: {len(DUMMY_SUBMISSION)} characters")
        print(f"   - Context Chunks: {len(DUMMY_CONTEXT)}")
        print()
        
        # Prepare inputs for the LangGraph workflow
        inputs = {
            "submission_text": DUMMY_SUBMISSION,
            "rubric": DUMMY_RUBRIC,
            "context": [],  # Will be populated by retrieve node
            "grade_result": None  # Will be populated by grade node
        }
        
        print("[>] Invoking LangGraph Workflow...")
        print()
        
        try:
            # Invoke the workflow
            result = agent.app.invoke(inputs)
            
            print()
            print("=" * 80)
            print("[OK] WORKFLOW EXECUTION SUCCESSFUL")
            print("=" * 80)
            print()
            
            # Extract the grade result
            grade_result: GradeResult = result["grade_result"]
            
            # Display results
            print("[RESULTS] GRADING RESULTS:")
            print("-" * 80)
            print(f"Score: {grade_result.score}/{sum(item.max_points for item in DUMMY_RUBRIC)}")
            print()
            print("Feedback:")
            print(grade_result.feedback)
            print()
            
            if grade_result.citations:
                print("Citations:")
                for i, citation in enumerate(grade_result.citations, 1):
                    print(f"  {i}. {citation}")
            else:
                print("Citations: None provided")
            
            print()
            print("=" * 80)
            print("[OK] TEST COMPLETED SUCCESSFULLY")
            print("=" * 80)
            
            # Validation checks
            print()
            print("[CHECK] Validation Checks:")
            max_score = sum(item.max_points for item in DUMMY_RUBRIC)
            
            checks = [
                ("Score is numeric", isinstance(grade_result.score, (int, float))),
                ("Score is within valid range", 0 <= grade_result.score <= max_score),
                ("Feedback is provided", len(grade_result.feedback) > 0),
                ("Citations is a list", isinstance(grade_result.citations, list)),
            ]
            
            for check_name, passed in checks:
                status = "[OK]" if passed else "[FAIL]"
                print(f"   {status} {check_name}")
            
            all_passed = all(passed for _, passed in checks)
            if all_passed:
                print()
                print("[SUCCESS] All validation checks passed!")
            else:
                print()
                print("[WARNING] Some validation checks failed!")
                
        except Exception as e:
            print()
            print("=" * 80)
            print("[ERROR] WORKFLOW EXECUTION FAILED")
            print("=" * 80)
            print(f"Error: {type(e).__name__}")
            print(f"Message: {str(e)}")
            import traceback
            print()
            print("Traceback:")
            traceback.print_exc()


if __name__ == "__main__":
    main()
