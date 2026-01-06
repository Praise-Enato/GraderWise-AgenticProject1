
import pandas as pd
import requests
import os
import json
import time

BASE_URL = "http://127.0.0.1:8000/grade"
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'synthetic_benchmarks.csv')

def run_stress_test():
    if not os.path.exists(DATA_PATH):
        print(f"Error: Data file not found at {DATA_PATH}")
        return

    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} synthetic submissions.")
    
    results = []

    for _, row in df.iterrows():
        student_id = row['student_id']
        essay_type = row['type']
        text = row['text']
        rubric = json.loads(row['rubric'])

        print(f"Testing: {essay_type}...")
        
        payload = {
            "submission_text": text,
            "rubric": rubric,
            "student_id": student_id
        }

        try:
            start_time = time.time()
            response = requests.post(BASE_URL, json=payload)
            response.raise_for_status()
            duration = time.time() - start_time
            
            data = response.json()
            score = data.get("score", 0)
            feedback = data.get("feedback", "")
            
            print(f"  -> Score: {score}/10 (Time: {duration:.2f}s)")
            
            result = {
                "type": essay_type,
                "score": score,
                "feedback": feedback,
                "pass": False,
                "reason": ""
            }

            # Assertions
            if student_id == "hallucinator":
                if score > 5:
                    result["pass"] = False
                    result["reason"] = "FAIL: Hallucination undetected (Score > 5)"
                    print(f"  FAILED: {result['reason']}")
                else:
                    result["pass"] = True
                    result["reason"] = "PASS: Hallucination penalized."
                    print("  PASS.")

            elif student_id == "cheat":
                if score > 2:
                    result["pass"] = False
                    result["reason"] = "FAIL: Irrelevance undetected (Score > 2)"
                    print(f"  FAILED: {result['reason']}")
                else:
                    result["pass"] = True
                    result["reason"] = "PASS: Irrelevance penalized."
                    print("  PASS.")
            
            elif student_id == "sloppy_genius":
                # Check for high score? Or just printing feedback as requested.
                # Assuming should be decent score but maybe not perfect due to grammar.
                print(f"\n[FEEDBACK FOR SLOPPY GENIUS]\n{feedback}\n")
                result["pass"] = True # No strict pass/fail criteria given for score, just feedback check.
                result["reason"] = "Feedback logged."
            
            elif student_id == "model_student":
                if score < 8:
                     result["pass"] = False
                     result["reason"] = f"FAIL: Model student scored too low ({score})"
                     print(f"  FAILED: {result['reason']}")
                else:
                     result["pass"] = True
                     result["reason"] = "PASS: Model student recognized."
                     print("  PASS.")
            
            results.append(result)

        except Exception as e:
            print(f"  ERROR: {e}")

    # Summary
    print("\n--- STRESS TEST SUMMARY ---")
    pass_count = sum(1 for r in results if r['pass'])
    print(f"Passed: {pass_count}/{len(results)}")
    
    if pass_count == len(results):
        print("RESULT: ALL TESTS PASSED")
    else:
        print("RESULT: FAILURES DETECTED")

if __name__ == "__main__":
    run_stress_test()
