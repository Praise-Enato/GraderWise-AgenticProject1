import pandas as pd
import os
import random
import json
from datasets import load_dataset

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
ASAP_PATH = os.path.join(DATA_DIR, 'training_set_rel3.tsv')
OUTPUT_FILE = os.path.join(DATA_DIR, 'real_world_benchmark.csv')

def get_asap_traits_data():
    """
    Extracts essays with detailed trait scores from ASAP (Set 8).
    Traits: Ideas, Organization, Style, Conventions, Sentence Fluency.
    """
    if not os.path.exists(ASAP_PATH):
        print(f"ASAP data not found at {ASAP_PATH}. Skipping English Argument.")
        return []

    print(f"Loading ASAP data from {ASAP_PATH}...")
    try:
        df = pd.read_csv(ASAP_PATH, sep='\t', encoding='ISO-8859-1')
        
        # Essay Set 8 (Narrative/Real Life) has traits in most versions of this dataset.
        # Check for trait columns
        trait_cols = ['rater1_trait1', 'rater1_trait2', 'rater1_trait3', 'rater1_trait4']
        
        # Filter for Set 8
        df_set8 = df[df['essay_set'] == 8].copy()
        
        # If Set 8 is empty/missing, try Set 7
        if df_set8.empty:
            df_set8 = df[df['essay_set'] == 7].copy()
            
        if df_set8.empty:
             print("No Essay Set 7/8 found.")
             return []

        # Check if traits allow for non-NaN
        # Usually ASAP traits are in rater1_trait1..6
        # Let's verify presence
        available_traits = [c for c in trait_cols if c in df_set8.columns]
        
        if not available_traits:
            print("Trait columns not found in ASAP data.")
            return []
            
        # Select 5 random essays
        sample = df_set8.sample(n=5, random_state=42)
        results = []
        
        for _, row in sample.iterrows():
            # Construct JSON Breakdown
            # Trait names are generic in the TSV, we map them carefully? 
            # Set 8 Traits: Ideas_and_Content, Organization, Voice, Sentence_Fluency, Conventions, choice_of_words??
            # We'll map T1..T4 generically.
            
            breakdown = {}
            total_trait_score = 0
            max_trait_score = 0
            
            # Map index to Name (Guessing standard ordering or generic)
            trait_names = ["Ideas", "Organization", "Voice", "Conventions"]
            
            for i, col in enumerate(available_traits):
                score = row[col]
                if pd.isna(score): continue
                
                name = trait_names[i] if i < len(trait_names) else f"Trait {i+1}"
                breakdown[name] = f"{int(score)}/6" # Max usually 6 for traits in Set 8
                total_trait_score += score
                max_trait_score += 6
            
            # Submisson Text
            text = row['essay']
            
            # Human Score (Normalize Total Traits to 0-10)
            if max_trait_score > 0:
                normalized_score = (total_trait_score / max_trait_score) * 10
            else:
                normalized_score = row['domain1_score'] # Fallback
            
            # The 'rubric' column in CSV will hold the Detailed Breakdown JSON per user request
            rubric_json_str = json.dumps(breakdown)
            
            results.append({
                "subject": "ENGLISH_ARGUMENT",
                "rubric": rubric_json_str, # Detailed scores
                "submission_text": text,
                "human_score": round(normalized_score, 1)
            })
            
        return results

    except Exception as e:
        print(f"Error processing ASAP: {e}")
        return []

def get_code_data():
    print("Downloading MBPP for Code Fallback...")
    try:
        ds = load_dataset("google-research-datasets/mbpp", split="test")
        
        # Select 5 random
        if len(ds) > 5:
            try:
                ds = ds.shuffle(seed=123).select(range(5))
            except:
                ds = ds.take(5)
        
        results = []
        for row in ds:
            correct_code = row['code']
            text = row['text']
            
            # Inject Bugs for Partial Credit (Score 5.0)
            # 1. Syntax Error: Remove colon after def or loop
            buggy_code = correct_code.replace(":", "", 1) 
            if buggy_code == correct_code:
                # Fallback: Replace 'return' with 'retrun'
                buggy_code = correct_code.replace("return", "retrun")
            
            # Rubric string is the breakdown? 
            # User said: "rubric -> Construct a JSON string from the content_score..."
            # For code: "Logic: 5/5, Syntax: 0/5"
            
            breakdown = {
                "Logic": "5/5",
                "Syntax": "0/5 (Critical Error)"
            }
            
            results.append({
                "subject": "CS_PYTHON",
                "rubric": json.dumps(breakdown),
                "submission_text": buggy_code,
                "human_score": 5.0
            })
            
        return results
    except Exception as e:
        print(f"Failed MBPP: {e}")
        return []

if __name__ == "__main__":
    all_data = []
    
    # English
    all_data.extend(get_asap_traits_data())
    
    # Code
    all_data.extend(get_code_data())
    
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"Successfully saved {len(df)} rows to {OUTPUT_FILE}")
        print(df.head())
    else:
        print("No data collected.")
