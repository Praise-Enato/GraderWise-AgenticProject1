import pandas as pd
import json
import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'training_set_rel3.tsv')
OUTPUT_PATH = os.path.join(BASE_DIR, 'data', 'asap_benchmark.csv')

def prepare_asap_data():
    print(f"Reading data from {DATA_PATH}...")
    # Read the TSV file with appropriate encoding
    df = pd.read_csv(DATA_PATH, sep='\t', encoding='ISO-8859-1')
    
    # Filter for Essay Set 1 (Comparisons/Computers)
    df_set1 = df[df['essay_set'] == 1].copy()
    
    # Take the first 10 essays
    benchmark_df = df_set1.head(10).copy()
    
    # Normalize Score: Original 2-12 -> 0-10
    # Formula: Score - 2
    benchmark_df['human_score_normalized'] = benchmark_df['rater1_domain1'] - 2
    
    # Hardcode the Rubric
    rubric_json = json.dumps([
        {
            "criteria": "Persuasive Argument",
            "max_points": 5,
            "description": "Clear stance with supporting reasons."
        },
        {
            "criteria": "Organization",
            "max_points": 5,
            "description": "Logical flow and transitions."
        }
    ])
    
    benchmark_df['rubric'] = rubric_json
    
    # Select columns
    final_df = benchmark_df[['essay_id', 'essay', 'rubric', 'human_score_normalized']]
    
    # Save to CSV
    print(f"Saving benchmark data to {OUTPUT_PATH}...")
    final_df.to_csv(OUTPUT_PATH, index=False)
    print("Done.")

if __name__ == "__main__":
    prepare_asap_data()
