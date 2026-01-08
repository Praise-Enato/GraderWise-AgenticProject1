import pandas as pd
import httpx
from groq import Groq
import os
import time
import json
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
INPUT_FILE = "backend/data/universal_benchmark.csv"
OUTPUT_FILE = "backend/data/universal_results.csv"
API_URL = "http://127.0.0.1:8000/grade"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("Error: GROQ_API_KEY environment variable not set.")
    # sys.exit(1) # Commented out to allow testing logic check even if key missing (will fail gracefully later)

client = Groq(api_key=GROQ_API_KEY)

def audit_feedback(submission, feedback):
    """
    Uses Llama-3.3-70b to evaluate the quality of the AI's feedback.
    """
    system_prompt = """You are an Expert Pedagogue and Quality Auditor. 
    Evaluate the following AI-generated feedback on a scale of 1-5 for:
    
    1. **Specificity**: Does it quote the text? Does it point to specific errors? (1=Vague, 5=Highly Specific)
    2. **Actionability**: Does it give a clear path to improvement/hint? (1=Unhelpful, 5=Clear Steps)
    3. **Tone**: Is it supportive and Socratic? (1=Harsh/Robotic, 5=Supportive Mentor)
    
    Output strictly in JSON:
    {
        "specificity": <int>,
        "actionability": <int>,
        "tone": <int>,
        "reasoning": "<brief explanation>"
    }
    """
    
    user_prompt = f"""
    STUDENT SUBMISSION:
    {submission}
    
    AI FEEDBACK:
    {feedback}
    
    Evaluate the feedback quality.
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"Audit Error: {e}")
        return {"specificity": 0, "actionability": 0, "tone": 0, "reasoning": "Error"}

def run_test():
    # 1. Load Data
    if not os.path.exists(INPUT_FILE):
        print(f"Input file not found: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    
    # 2. Checkpoint
    processed_indices = set()
    if os.path.exists(OUTPUT_FILE):
        existing_df = pd.read_csv(OUTPUT_FILE)
        # Assuming we just append validation rows, mapped roughly by 'original_index' or just count.
        # Since CSV doesn't have ID, we'll skip first N rows where N is len(existing_df) 
        # IF the files align perfectly. Safer: Checkpoint by appending.
        # The simplest way without unique IDs is just to re-process or append and assume order.
        # Let's count existing rows.
        rows_done = len(existing_df)
        print(f"Found {rows_done} existing results. Skipping...")
        df = df.iloc[rows_done:]
    else:
        # Initialize file with headers
        with open(OUTPUT_FILE, 'w') as f:
            f.write("subject,human_score,ai_score,score_error,specificity,actionability,tone\n")

    print(f"Starting benchmark on {len(df)} rows...")
    
    # 3. Loop
    for index, row in df.iterrows():
        subject = row['subject']
        submission_text = row['submission_text']
        # Construct rubric list for payload
        rubric_description = row['rubric'] + f". Ground Truth: {row['ground_truth']}"
        rubric_payload = [
            {
                "criteria": "Accuracy",
                "description": rubric_description,
                "max_points": 10
            }
        ]
        
        # Assumption: Submissions are correct correct answers (simulated), so human_score=10.
        human_score = 10.0 
        
        # Step A: Grade
        ai_score = 0.0
        feedback = ""
        
        try:
            # Retry loop for API
            for attempt in range(2):
                try:
                    response = httpx.post(
                        API_URL, 
                        json={
                            "submission_text": submission_text,
                            "rubric": rubric_payload,
                            "student_id": "test_user_001"
                        }, 
                        timeout=60.0
                    )
                    if response.status_code == 200:
                        data = response.json()
                        # FastAPI returns the model directly, not nested
                        ai_score = data.get("score", 0.0)
                        feedback = data.get("feedback", "")
                        break
                    elif response.status_code == 429:
                        print("429 Rate Limit from Agent. Sleeping 60s...")
                        time.sleep(60)
                        continue
                    elif response.status_code >= 500:
                        print(f"500 Server Error. Retrying in 10s... ({attempt+1}/2)")
                        time.sleep(10)
                        continue
                except httpx.RequestError as e:
                    print(f"Request Error: {e}")
                    time.sleep(5)
        except Exception as e:
            print(f"Grading failed completely: {e}")
            
        # Step B: Audit
        audit_metrics = {"specificity": 0, "actionability": 0, "tone": 0}
        if feedback:
            try:
                # Rate limit for Groq
                audit_metrics = audit_feedback(submission_text, feedback)
            except Exception as e:
                print(f"Audit failed: {e}")
        
        # Step C: Save
        score_error = abs(human_score - ai_score)
        
        result_row = {
            "subject": subject,
            "human_score": human_score,
            "ai_score": ai_score,
            "score_error": score_error,
            "specificity": audit_metrics.get("specificity", 0),
            "actionability": audit_metrics.get("actionability", 0),
            "tone": audit_metrics.get("tone", 0)
        }
        
        # Append to CSV immediately
        result_df = pd.DataFrame([result_row])
        result_df.to_csv(OUTPUT_FILE, mode='a', header=False, index=False)
        
        print(f"Processed {subject}: AI={ai_score}, Human={human_score}, Spec={result_row['specificity']}")
        if ai_score < 5:
            print(f"  [DEBUG] Low Score Feedback: {feedback[:200]}...")
        
        # Throttle
        time.sleep(5) 

    # 4. Final Report
    print("\n=== FINAL BENCHMARK REPORT ===")
    if os.path.exists(OUTPUT_FILE):
        results = pd.read_csv(OUTPUT_FILE)
        if not results.empty:
            summary = results.groupby("subject").agg({
                "score_error": "mean",
                "specificity": "mean",
                "tone": "mean",
                "ai_score": "count" # N
            }).rename(columns={"score_error": "MAE", "ai_score": "N"})
            
            print(summary)
            
            print("\nOverall Metrics:")
            print(f"Total MAE: {results['score_error'].mean():.2f}")
            print(f"Avg Specificity: {results['specificity'].mean():.2f}")
            print(f"Avg Tone: {results['tone'].mean():.2f}")
        else:
            print("No results found.")

if __name__ == "__main__":
    run_test()
