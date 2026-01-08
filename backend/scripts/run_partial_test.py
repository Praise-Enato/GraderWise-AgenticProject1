import pandas as pd
import httpx
import os
import time
import json
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
INPUT_FILE = "backend/data/universal_partial.csv"
OUTPUT_FILE = "backend/data/universal_partial_results.csv"
API_URL = "http://127.0.0.1:8000/grade"

def run_test():
    # 1. Load Data
    if not os.path.exists(INPUT_FILE):
        print(f"Input file not found: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    
    # 2. Checkpoint
    if os.path.exists(OUTPUT_FILE):
        try:
             # Just overwrite for this small test to avoid checking logic complexity
             pass
        except:
             pass
    
    # Initialize file with headers
    with open(OUTPUT_FILE, 'w') as f:
        f.write("subject,expected_score,ai_score,score_error,notes\n")

    print(f"Starting PARTIAL CREDIT TEST on {len(df)} rows...")
    
    # 3. Loop
    for index, row in df.iterrows():
        subject = row['subject']
        submission_text = row['submission_text']
        rubric_description = row['rubric'] + f". Ground Truth: {row['ground_truth']}"
        rubric_payload = [
            {
                "criteria": "Accuracy",
                "description": rubric_description,
                "max_points": 10
            }
        ]
        
        expected_score = float(row['expected_score'])
        
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
                            "student_id": "test_partial_user"
                        }, 
                        timeout=60.0
                    )
                    if response.status_code == 200:
                        data = response.json()
                        ai_score = data.get("score", 0.0)
                        feedback = data.get("feedback", "")
                        break
                    elif response.status_code == 429:
                        print("429 Rate Limit. Sleeping 60s...")
                        time.sleep(60)
                        continue
                    elif response.status_code >= 500:
                        print(f"500 Server Error. Retrying... ({attempt+1}/2)")
                        time.sleep(5)
                        continue
                except httpx.RequestError as e:
                    print(f"Request Error: {e}")
                    time.sleep(5)
        except Exception as e:
            print(f"Grading failed: {e}")
            
        # Step C: Save
        score_error = abs(expected_score - ai_score)
        
        # Escape comma in notes
        notes = str(row.get('notes', '')).replace(",", ";").replace("\n", " ")
        
        result_row = f"{subject},{expected_score},{ai_score},{score_error},{notes}\n"
        
        with open(OUTPUT_FILE, 'a') as f:
            f.write(result_row)
        
        print(f"Processed {subject}: Exp={expected_score}, AI={ai_score}, Error={score_error}")
        
        # Throttle
        time.sleep(2) 

    # 4. Final Report
    print("\n=== FINAL PARTIAL TEST REPORT ===")
    if os.path.exists(OUTPUT_FILE):
        results = pd.read_csv(OUTPUT_FILE)
        if not results.empty:
            mae = results['score_error'].mean()
            print(f"Mean Absolute Error: {mae:.2f}")
            print("\nDistribution:")
            print(results[['subject', 'expected_score', 'ai_score']])
        else:
            print("No results found.")

if __name__ == "__main__":
    run_test()
