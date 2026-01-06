
import os
import json
import random
import pandas as pd
import httpx
from dotenv import load_dotenv
from groq import Groq

# Setup
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("Error: GROQ_API_KEY not found in environment variables.")
    exit(1)

client = Groq(api_key=GROQ_API_KEY)
# Note: Using a fixed student_id for audit purposes
STUDENT_ID = "audit_student_001" 
BASE_URL = "http://127.0.0.1:8000/grade"
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'asap_benchmark.csv')
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'feedback_audit.csv')

def get_grader_feedback(essay_text, rubric):
    rubric_obj = json.loads(rubric)
    payload = {
        "submission_text": essay_text,
        "rubric": rubric_obj,
        "student_id": STUDENT_ID
    }
    
    try:
        response = httpx.post(BASE_URL, json=payload, timeout=120.0)
        response.raise_for_status()
        data = response.json()
        # Revert to direct access as per main.py response_model=GradeResult
        score = data.get("score", 0)
        feedback = data.get("feedback", "")
        
        if not feedback:
            print(f"DEBUG: Empty feedback received. Full Response keys: {data.keys()}")
            print(f"DEBUG: Data snippet: {str(data)[:200]}")
            
        return feedback, score
    except Exception as e:
        print(f"Error getting grader feedback: {e}")
        return None, None

def judge_feedback(essay_text, ai_feedback):
    system_prompt = (
        "You are an independent educational auditor. Your job is to critique the feedback provided by an AI Teaching Assistant. "
        "You must be CRITICAL and HARSH. Do not give perfect scores unless the feedback is truly exceptional. "
        "Output ONLY a valid JSON object."
    )
    
    user_prompt = f"""
    STUDENT ESSAY (Excerpt):
    {essay_text[:500]}...
    
    AI TEACHING ASSISTANT FEEDBACK:
    {ai_feedback}
    
    TASK:
    Analyze the feedback and output a JSON object with these integer ratings (1-5):
    
    "specificity": (Does it quote the student's text? 1-5)
    "actionability": (Does it tell the student exactly how to fix the error? 1-5)
    "tone": (Is it professional and encouraging? 1-5)
    "reasoning": "A one sentence explanation of your ratings."
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"Error calling Judge: {e}")
        return None

def main():
    if not os.path.exists(DATA_PATH):
        print(f"Error: Data file not found at {DATA_PATH}")
        return

    print("Loading data...")
    df = pd.read_csv(DATA_PATH)
    
    # Sample 5 random essays
    sample_df = df.sample(n=5)
    
    audit_results = []
    
    for _, row in sample_df.iterrows():
        essay_id = row['essay_id']
        essay_text = row['essay']
        rubric = row['rubric']
        
        print(f"\n--- Auditing Essay ID: {essay_id} ---")
        print(f"Essay Excerpt: {essay_text[:100]}...")
        
        # Step A: Get Grader Feedback
        print("requesting grader feedback...")
        ai_feedback, ai_score = get_grader_feedback(essay_text, rubric)
        
        if not ai_feedback:
            print("Skipping due to grader error.")
            continue
            
        print(f"AI Feedback: {ai_feedback[:150]}...")
        
        # Step B: Judge
        print("Judge is evaluating...")
        judge_result = judge_feedback(essay_text, ai_feedback)
        
        if judge_result:
            print(f"Judge Ratings: {judge_result}")
            audit_results.append({
                "essay_id": essay_id,
                "ai_score": ai_score,
                "ai_feedback": ai_feedback,
                "specificity": judge_result.get("specificity"),
                "actionability": judge_result.get("actionability"),
                "tone": judge_result.get("tone"),
                "reasoning": judge_result.get("reasoning")
            })
        else:
            print("Judge failed to return valid JSON.")

    # Save Results
    if audit_results:
        results_df = pd.DataFrame(audit_results)
        # If file exists, append without header
        header = not os.path.exists(OUTPUT_PATH)
        results_df.to_csv(OUTPUT_PATH, mode='a', header=header, index=False)
        print(f"\nSaved audit results to {OUTPUT_PATH}")
        
        # Calculate Averages
        avg_spec = results_df['specificity'].mean()
        avg_act = results_df['actionability'].mean()
        avg_tone = results_df['tone'].mean()
        
        print("\n--- AUDIT REPORT SUMMARY ---")
        print(f"Average Specificity: {avg_spec:.2f}/5")
        print(f"Average Actionability: {avg_act:.2f}/5")
        print(f"Average Tone: {avg_tone:.2f}/5")
        
        if avg_spec < 3 or avg_act < 3:
            print("\nWARNING: Feedback quality is low in Specificity or Actionability.")
    else:
        print("\nNo audit results generated.")

if __name__ == "__main__":
    main()
