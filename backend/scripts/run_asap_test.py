import pandas as pd
import httpx
import asyncio
import json
import os
import sys

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'asap_benchmark.csv')

API_URL = "http://127.0.0.1:8000/grade"

async def grade_essay(client, essay_id, text, rubric):
    try:
        payload = {
            "submission_text": text,
            "rubric": json.loads(rubric) if isinstance(rubric, str) else rubric,
            "student_id": str(essay_id)
        }
        
        response = await client.post(API_URL, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error grading essay {essay_id}: {e}")
        return None

async def run_benchmark():
    if not os.path.exists(DATA_PATH):
        print(f"Error: {DATA_PATH} not found. Run prepare_asap.py first.")
        return

    print(f"Loading benchmark data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    
    results = []
    total_error = 0
    valid_count = 0
    
    print(f"Starting benchmark on {len(df)} essays...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for index, row in df.iterrows():
            essay_id = row['essay_id']
            human_score = row['human_score_normalized']
            
            print(f"Grading Essay ID: {essay_id}...")
            
            ai_result = await grade_essay(client, essay_id, row['essay'], row['rubric'])
            
            if ai_result:
                ai_score = ai_result.get('score', 0)
                error = abs(ai_score - human_score)
                
                results.append({
                    "Essay ID": essay_id,
                    "Human Score": human_score,
                    "AI Score": ai_score,
                    "Abs Error": error
                })
                
                total_error += error
                valid_count += 1
            else:
                 results.append({
                    "Essay ID": essay_id,
                    "Human Score": human_score,
                    "AI Score": "ERROR",
                    "Abs Error": "N/A"
                })

    # Prepare markdown table
    output_lines = []
    output_lines.append("### Benchmark Results")
    output_lines.append("| Essay ID | Human Score | AI Score | Abs Error |")
    output_lines.append("|----------|-------------|----------|-----------|")
    for r in results:
        output_lines.append(f"| {r['Essay ID']} | {r['Human Score']} | {r['AI Score']} | {r['Abs Error']} |")
    
    if valid_count > 0:
        mae = total_error / valid_count
        output_lines.append(f"\n**Mean Absolute Error (MAE): {mae:.2f}**")
    else:
        output_lines.append("\nNo valid results to calculate MAE.")

    output_text = "\n".join(output_lines)
    print("\n" + output_text)

    # Save to CSV
    if valid_count > 0:
        mae = total_error / valid_count
        results.append({
            "Essay ID": "Mean Absolute Error (MAE)",
            "Human Score": "",
            "AI Score": "",
            "Abs Error": round(mae, 2)
        })

    results_df = pd.DataFrame(results)
    results_path = os.path.join(BASE_DIR, 'data', 'benchmark_results.csv')
    results_df.to_csv(results_path, index=False)
    print(f"\nResults saved to {results_path}")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
