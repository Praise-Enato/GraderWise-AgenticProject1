import sys
import os

# Add the project root to the python path so imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.src.agent import app 
from backend.src.models import RubricItem, GradeResult

def test_chat_logic():
    print("=== TEST START: Conversational Agent Logic ===")
    
    # Define a simple rubric
    rubric = [
        RubricItem(criteria="Correctness", max_points=10.0, description="The code must run correctly and produce the expected output."),
        RubricItem(criteria="Style", max_points=5.0, description="Code should be readable.")
    ]
    
    # --- Turn 1: The Submission ---
    print("\n--- TURN 1: SUBMISSION ---")
    submission_text = """
def add(x, y):
    return x - y # Should be plus!
"""
    print(f"Input Submission: {submission_text.strip()}")
    
    # Initial State for submission
    state_v1 = {
        "submission_text": submission_text,
        "rubric": rubric,
        "messages": [], # No history yet
        "grade_data": {} # Empty
    }
    
    print("Invoking Agent (Grading Flow)...")
    result_v1 = app.invoke(state_v1)
    
    grade_data = result_v1.get("grade_data", {})
    final_feedback = result_v1.get("final_feedback", "")
    
    print(f"Turn 1 Result Score: {grade_data.get('score')}")
    print(f"Turn 1 Feedback Triggered: {bool(final_feedback)}")
    
    if not grade_data or grade_data.get("score") is None:
        print("❌ FAILED: Grade data not produced in Turn 1.")
        return

    print("✅ Turn 1 Completed. Grade captured.")

    # --- Turn 2: The Follow-up Question ---
    print("\n--- TURN 2: FOLLOW-UP QUESTION ---")
    question_text = "Why did I lose points? I don't understand."
    print(f"User Question: {question_text}")
    
    # Construct State for Turn 2
    # CRITICAL: Injecting the previous grade_data and adding the question to messages
    state_v2 = {
        "submission_text": submission_text, # Keep context (optional but good practice)
        "rubric": rubric,
        "grade_data": grade_data, # INJECTED MEMORY
        "messages": [
            # In a real app, we'd have the history. simulating just the new question for simplicity of the test
            {"role": "user", "content": question_text} 
        ]
    }
    
    print("Invoking Agent (Q&A Flow)...")
    result_v2 = app.invoke(state_v2)
    
    tutor_response = result_v2.get("final_feedback", "")
    new_grade_data = result_v2.get("grade_data", {})
    
    # Verification
    print("\n--- VERIFICATION ---")
    print(f"Tutor Response:\n{tutor_response}")
    
    # Check that score didn't change (identity check or value check)
    # The agent might return the same grade_data object or a copy, but the router should have skipped 'grade_submission' node.
    # We can check the 'thinking_process' to see if grading occurred.
    
    thinking = result_v2.get("thinking_process", [])
    print(f"Thinking Process: {thinking}")
    
    if "---GRADING SUBMISSION" in str(thinking) or "Grading Attempt" in str(thinking):
         print("❌ FAILED: The agent re-graded the submission instead of just tutoring.")
    else:
         print("✅ SUCCESS: The agent skipped grading.")
         
    if "Score: " in tutor_response or "Critique:" in tutor_response:
        # A rough check if it looks like feedback
        pass
        
    if "can't answer questions yet" in tutor_response:
        print("❌ FAILED: Agent claimed relevant data was missing.")
    else:
        print("✅ SUCCESS: Agent answered the question.")

if __name__ == "__main__":
    test_chat_logic()
