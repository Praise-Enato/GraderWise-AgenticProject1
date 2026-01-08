import pandas as pd
import httpx
import os
import time
import json
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
INPUT_FILE = "backend/data/real_world_benchmark.csv"
OUTPUT_FILE = "backend/data/real_world_results.csv"
API_URL = "http://127.0.0.1:8000/grade"

def parse_rubric_json(rubric_str):
    """
    Parses the JSON rubric string from the CSV and converts it into 
    a list of RubricItem dicts for the API.
    Example Input (JSON): {"Ideas": "5/6", "Org": "4/6"}
    Example Output: [
       {"criteria": "Ideas", "max_points": 10, "description": "Evaluate Ideas. Reference Score: 5/6"},
       ...
    ]
    Note: We normalize max_points to 10 for consistency since the Agent is 0-10 based, 
    OR we can keep specific max_points if the Agent supports it. 
    The Agent flattens points, but let's just make it descriptive.
    Actually, let's try to pass the precise max points from the string if parseable (e.g. "/6").
    """
    try:
        data = json.loads(rubric_str)
        items = []
        for criteria, score_str in data.items():
            # Try to extract max points from "X/Y"
            max_pts = 10
            if "/" in str(score_str):
                try:
                    parts = str(score_str).split("/")
                    # Cleaning string like "5/5 (Critical Error)"
                    denom = re.search(r'\d+', parts[1])
                    if denom:
                        max_pts = int(denom.group(0))
                except:
                    pass
            
            items.append({
                "criteria": criteria,
                "description": f"Evaluate this aspect. (Reference/Ground Truth range: {score_str})",
                "max_points": max_pts
            })
        return items
    except Exception as e:
        print(f"Error parsing rubric: {e}")
        # Fallback
        return [{"criteria": "General Quality", "description": rubric_str, "max_points": 10}]

def run_test():
    # 1. Load Data
    if not os.path.exists(INPUT_FILE):
        print(f"Input file not found: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    
    # Initialize file with headers
    with open(OUTPUT_FILE, 'w') as f:
        f.write("subject,human_score,ai_score,score_error,breakdown_notes\n")

    print(f"Starting REAL WORLD TEST on {len(df)} rows...")
    
    # 3. Loop
    for index, row in df.iterrows():
        subject = row['subject']
        submission_text = row['submission_text']
        rubric_str = row['rubric']
        human_score = float(row['human_score'])
        
        # Construct Rubric Payload
        rubric_payload = parse_rubric_json(rubric_str)
        
        # Step A: Grade
        ai_score = 0.0
        feedback = ""
        rubric_perf = {}
        
        try:
            # Retry loop
            for attempt in range(2):
                try:
                    response = httpx.post(
                        API_URL, 
                        json={
                            "submission_text": submission_text,
                            "rubric": rubric_payload,
                            "student_id": "test_real_user"
                        }, 
                        timeout=60.0
                    )
                    if response.status_code == 200:
                        data = response.json()
                        ai_score = data.get("score", 0.0)
                        feedback = data.get("feedback", "")
                        rubric_perf = data.get("rubric_performance", {})
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
        score_error = abs(human_score - ai_score)
        
        # Serialize rubric performance for CSV
        breakdown_str = json.dumps(rubric_perf).replace(",", ";")
        
        result_row = f"{subject},{human_score},{ai_score},{score_error},{breakdown_str}\n"
        
        with open(OUTPUT_FILE, 'a') as f:
            f.write(result_row)
        
        print(f"Processed {subject}: Human={human_score}, AI={ai_score}, Error={score_error}")
        
        # Throttle
        time.sleep(2) 

    # 4. Final Report
    print("\n=== FINAL REAL WORLD TEST REPORT ===")
    if os.path.exists(OUTPUT_FILE):
        results = pd.read_csv(OUTPUT_FILE)
        if not results.empty:
            mae = results['score_error'].mean()
            print(f"Mean Absolute Error: {mae:.2f}")
            print("\nDistribution:")
            print(results[['subject', 'human_score', 'ai_score']])
        else:
            print("No results found.")

if __name__ == "__main__":
    run_test()
