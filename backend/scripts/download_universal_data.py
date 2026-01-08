import os
import pandas as pd
from datasets import load_dataset
import random

# Ensure output directory exists
OUTPUT_DIR = "backend/data"
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "universal_benchmark.csv")

MMLU_STEM = [
    'abstract_algebra', 'anatomy', 'astronomy', 'college_biology', 
    'college_chemistry', 'college_computer_science', 'college_mathematics', 
    'college_medicine', 'college_physics', 'computer_security', 
    'electrical_engineering'
]

MMLU_HUMANITIES = [
    'high_school_european_history', 'high_school_us_history', 
    'high_school_world_history', 'international_law', 'jurisprudence', 
    'philosophy', 'prehistory', 'professional_law', 'sociology'
]

def get_mmlu_subset(subset_name):
    print(f"Downloading MMLU subset: {subset_name}")
    try:
        ds = load_dataset("cais/mmlu", subset_name, split="test")
        
        # Select 4 random examples
        if len(ds) > 4:
            try:
                ds = ds.shuffle(seed=42).select(range(4))
            except:
                ds = ds.take(4)
        
        results = []
        for row in ds:
            question = row['question']
            choices = row['choices']
            answer_idx = row['answer']
            correct_text = choices[answer_idx]
            
            # Simulate a student submission that is correct
            submission_simulated = f"The correct answer is {correct_text}. This is the best choice based on the standard principles of the field."
            
            results.append({
                "subject": subset_name,
                "rubric": f"Rubric: Answer the following question accurately: {question}",
                "submission_text": submission_simulated,
                "ground_truth": correct_text
            })
        return results
    except Exception as e:
        print(f"Failed {subset_name}: {e}")
        return []

def get_mbpp():
    print("Downloading MBPP (Coding)")
    try:
        ds = load_dataset("google-research-datasets/mbpp", split="test")
         # Select 5 random examples
        if len(ds) > 5:
            try:
                ds = ds.shuffle(seed=42).select(range(5))
            except:
                ds = ds.take(5)
            
        results = []
        for row in ds:
            code = row['code']
            text = row['text']
            
            results.append({
                "subject": "python_coding",
                "rubric": f"Rubric: Write a Python function to: {text}",
                "submission_text": code, # The code itself is the submission
                "ground_truth": code
            })
        return results
    except Exception as e:
        print(f"Failed MBPP: {e}")
        return []

if __name__ == "__main__":
    all_data = []
    
    # Process MMLU Subsets
    for s in MMLU_STEM:
        all_data.extend(get_mmlu_subset(s))
        
    for s in MMLU_HUMANITIES:
        all_data.extend(get_mmlu_subset(s))
        
    # Process MBPP
    all_data.extend(get_mbpp())
    
    # Save Combined
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"Successfully saved {len(df)} rows to {OUTPUT_FILE}")
    else:
        print("No data collected.")
