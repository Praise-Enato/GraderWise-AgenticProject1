import pandas as pd
import os
import random
import json
from groq import Groq
from dotenv import load_dotenv

# Load environment variables (for GROQ_API_KEY)
load_dotenv()

# Configuration
INPUT_FILE = "backend/data/universal_benchmark.csv"
OUTPUT_FILE = "backend/data/universal_partial.csv"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("Error: GROQ_API_KEY environment variable not set.")
    # In production, we might exit, but for dev we'll let it fail later if needed

client = Groq(api_key=GROQ_API_KEY)

# Subject Categories for Prompt Logic
STEM_SUBJECTS = [
    'abstract_algebra', 'anatomy', 'astronomy', 'college_biology', 
    'college_chemistry', 'college_computer_science', 'college_mathematics', 
    'college_medicine', 'college_physics', 'computer_security', 
    'electrical_engineering'
]

HUMANITIES_SUBJECTS = [
    'high_school_european_history', 'high_school_us_history', 
    'high_school_world_history', 'international_law', 'jurisprudence', 
    'philosophy', 'prehistory', 'professional_law', 'sociology'
]

CODING_SUBJECTS = ['python_coding']

def get_flaw_instruction(subject):
    if subject in STEM_SUBJECTS:
        return "Perform the correct steps but make a calculation error in the final line or at the middle. The answer should be mostly correct logic-wise but numerically wrong."
    elif subject in CODING_SUBJECTS:
        return "Write correct logic but include one syntax error (missing colon, wrong indentation) or variable name mismatch (using 'x' instead of 'count')."
    elif subject in HUMANITIES_SUBJECTS:
        return "State the correct fact but fail to explain why it matters (shallow analysis). Mention the key terms but provide no depth or connecting arguments."
    else:
        return "Provide a mostly correct answer but omit one key detail."

def generate_partial_submission(row):
    subject = row['subject']
    rubric_text = row['rubric']
    ground_truth = row['ground_truth']
    
    # Target random score between 2 and 8 (represented as 20% to 80%)
    target_score = random.randint(2, 8)
    flaw_instruction = get_flaw_instruction(subject)
    
    system_prompt = f"""You are a Student Simulator and Grader.
    Your goal is to write a student submission that deserves a score of {target_score}/10 (Partial Credit).
    
    The grading rubric has 5 parts (2 marks each). You should succeed in roughly {target_score//2} parts and fail in the rest.
    
    SUBJECT: {subject}
    FLAW INSTRUCTION: {flaw_instruction}
    
    Output strictly in JSON format:
    {{
        "submission_text": "The student's imperfect answer...",
        "generated_rubric_notes": "Brief notes on what rubrics were met/missed to justify score {target_score}"
    }}
    """
    
    user_prompt = f"""
    QUESTION/RUBRIC: {rubric_text}
    PERFECT GROUND TRUTH: {ground_truth}
    
    Generate the partial credit submission.
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content), target_score
    except Exception as e:
        print(f"Error generating partial answer for {subject}: {e}")
        return None, 0

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Input file not found: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    
    # Group by subject and take 2 random examples from each
    selected_rows = []
    grouped = df.groupby('subject')
    
    for subject, group in grouped:
        # Take up to 2 examples
        sample = group.sample(n=min(2, len(group)), random_state=42)
        selected_rows.append(sample)
        
    if not selected_rows:
        print("No data found.")
        return

    subset_df = pd.concat(selected_rows)
    print(f"Selected {len(subset_df)} examples for partial data generation.")
    
    results = []
    
    for index, row in subset_df.iterrows():
        print(f"Generating partial answer for {row['subject']}...")
        generated_data, target_score = generate_partial_submission(row)
        
        if generated_data:
            results.append({
                "subject": row['subject'],
                "rubric": row['rubric'], # Keep original question
                "submission_text": generated_data.get("submission_text", ""),
                "ground_truth": row['ground_truth'],
                "expected_score": target_score,
                "notes": generated_data.get("generated_rubric_notes", "")
            })
            
    # Save to CSV
    if results:
        result_df = pd.DataFrame(results)
        result_df.to_csv(OUTPUT_FILE, index=False)
        print(f"Successfully saved {len(result_df)} partial credit examples to {OUTPUT_FILE}")
    else:
        print("Failed to generate any data.")

if __name__ == "__main__":
    main()
