import os
import pandas as pd
from datasets import load_dataset
import random

# Ensure output directory exists
OUTPUT_DIR = "backend/data"
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "universal_failures.csv")

# Same subsets as universal_benchmark to ensure comparable coverage
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

GENERIC_WRONG_REASONING = [
    "it intuitively feels correct based on general knowledge",
    "I recall reading this in a different textbook",
    "process of elimination suggests the other options are too unlikely",
    "it seems to align best with the theory, despite the complexity",
    "it is the most common answer in similar problems"
]

def get_mmlu_failure_subset(subset_name):
    print(f"Generating FAILURES for MMLU subset: {subset_name}")
    try:
        ds = load_dataset("cais/mmlu", subset_name, split="test")
        
        # Select 4 random examples
        if len(ds) > 4:
            try:
                ds = ds.shuffle(seed=99).select(range(4)) # Different seed than success data
            except:
                ds = ds.take(4)
        
        results = []
        for row in ds:
            question = row['question']
            choices = row['choices']
            correct_idx = row['answer']
            
            # THE SWITCH: Pick a Wrong Index
            options = [0, 1, 2, 3] # MMLU has 4 choices usually (A,B,C,D)
            # Filter out the correct one
            wrong_indices = [i for i in range(len(choices)) if i != correct_idx]
            
            if not wrong_indices:
                continue # Should not happen unless only 1 choice
                
            wrong_idx = random.choice(wrong_indices)
            wrong_text = choices[wrong_idx]
            correct_text = choices[correct_idx]
            
            # Synthetic Wrong Reasoning
            reasoning = random.choice(GENERIC_WRONG_REASONING)
            
            submission_text = f"I believe the answer is {wrong_text} because {reasoning}."
            
            results.append({
                "subject": subset_name,
                "rubric": f"Rubric: Answer the following question accurately: {question}",
                "submission_text": submission_text,
                "ground_truth": correct_text,
                "human_score": 0.0 # FAIL
            })
        return results
    except Exception as e:
        print(f"Failed {subset_name}: {e}")
        return []

if __name__ == "__main__":
    all_data = []
    
    # Process MMLU Subsets
    for s in MMLU_STEM:
        all_data.extend(get_mmlu_failure_subset(s))
        
    for s in MMLU_HUMANITIES:
        all_data.extend(get_mmlu_failure_subset(s))
        
    # Note: We are strictly doing MMLU here as requested by the "Switch" logic (Indices).
    
    # Save Combined
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"Successfully saved {len(df)} FAILURE rows to {OUTPUT_FILE}")
    else:
        print("No data collected.")
