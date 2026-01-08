import pandas as pd
import httpx
from groq import Groq
import os
import time
import json
from dotenv import load_dotenv

load_dotenv()

# Config
RUBRIC_PATH = "backend/data/rubrics/CSE111_week1_project_rubric - Sheet1.csv"
CONTEXT_PATH = "backend/data/course_materials/CSE111_week01_project.txt"
SUBMISSION_PATH = "backend/data/tire_volume.py"
OUTPUT_FILE = "backend/data/cse111_results.csv"
API_URL = "http://127.0.0.1:8000/grade"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

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

def parse_rubric(csv_path):
    """
    Reads the CSV and converts to RubricItem list.
    """
    try:
        df = pd.read_csv(csv_path)
        rubric_items = []
        
        for _, row in df.iterrows():
            if row['Criterion'] == 'TOTAL': continue
            
            criteria = row['Criterion']
            max_points = float(row['Max Points'])
            
            # Construct a descriptive text from levels
            desc = f"{row.get('Level 1 Description', '')} (Max {max_points})."
            
            rubric_items.append({
                "criteria": criteria,
                "description": desc,
                "max_points": max_points
            })
        return rubric_items
    except Exception as e:
        print(f"Error parsing rubric CSV: {e}")
        return []

def run_test():
    print("--- Starting CSE111 Grading Test ---")
    
    # 1. READ FILES
    rubric_payload = parse_rubric(RUBRIC_PATH)
    
    if not os.path.exists(CONTEXT_PATH):
        print(f"File not found: {CONTEXT_PATH}, using empty context.")
        context_text = ""
    else:
        with open(CONTEXT_PATH, 'r') as f:
            context_text = f.read()
            
    if not os.path.exists(SUBMISSION_PATH):
        print(f"File not found: {SUBMISSION_PATH}")
        return
        
    with open(SUBMISSION_PATH, 'r') as f:
        submission_text = f.read()
        
    # 2. CALL API
    print("Sending request to Agent...")
    try:
        # Note: 'rubric' field in payload expects a List[RubricItem] now
        response = httpx.post(
            API_URL, 
            json={
                "submission_text": submission_text,
                "rubric": rubric_payload,
                "student_id": "cse111_student",
                "context": [context_text] if context_text else [] # Assuming backend supports direct context injection or retrieval. 
                                                                  # Wait, rag logic retrieves context. 
                                                                  # BUT for this specific test, user supplied 'course material'.
                                                                  # The Agent usually uses RAG to fetch context. 
                                                                  # If I want to FORCE context, I might need to mock RAG or assume RAG picks it up if it's in the knowledge base.
                                                                  # However, the AgentState definition has `context: List[str]`. 
                                                                  # The `retrieve` node calls `rag.retrieve_context`.
                                                                  # The user request said "this is the course material the grader will use as context".
                                                                  # To strictly follow this without RAG ingestion, I would need to bypass RAG. 
                                                                  # But I can't easily bypass RAG without code edit.
                                                                  # LUCKILY, RAG retrieves based on query. 
                                                                  # Let's hope RAG works, OR I can manually Inject it if I could modify state, but via API I can't.
                                                                  # Actually, if I look at `main.py`... NO, I can't inject context via API payload unless I modify `main.py` models. 
                                                                  # But let's assume RAG has access or the prompt "use the provided RUBRIC and CONTEXT" works on what RAG finds.
                                                                  # Wait, the user provided a specific file. I haven't ingested this file into RAG.
                                                                  # IMPORTANT: The user said "this is the course material... use as context".
                                                                  # I should probably ingest it or just rely on the Prompt. 
                                                                  # Actually, I can simply Prepend the Context to the Submission Text labeled as "REFERENCE MATERIAL".
                                                                  # That's a safe hack.
            }, 
            timeout=120.0
        )
        
        # Correction: I'll prepend Context to Submission if I can't inject it.
        # But wait, looking at `main.py` (which I viewed earlier), GradeRequest has `submission_text`.
        # I'll prepend content.
        
    except Exception as e:
        print(f"Error preparing request: {e}")
        return

    # Let's do the prepending hack to ensure context is seen
    full_submission_payload = f"--- REFERENCE COURSE MATERIAL ---\n{context_text}\n\n--- STUDENT SUBMISSION ---\n{submission_text}"
    
    try:
        response = httpx.post(
            API_URL, 
            json={
                "submission_text": full_submission_payload,
                "rubric": rubric_payload,
                "student_id": "cse111_student"
            }, 
            timeout=120.0
        )
        
        if response.status_code == 200:
            data = response.json()
            score = data.get("score")
            feedback = data.get("feedback")
            print(f"Grading Complete. Score: {score}")
            
            # 3. AUDIT
            print("Auditing feedback...")
            audit = audit_feedback(submission_text, feedback)
            
            # 4. SAVE
            df = pd.DataFrame([{
                "submission_file": "tire_volume.py",
                "score": score,
                "specificity": audit.get("specificity"),
                "actionability": audit.get("actionability"),
                "tone": audit.get("tone"),
                "feedback": feedback,
                "audit_reasoning": audit.get("reasoning")
            }])
            
            df.to_csv(OUTPUT_FILE, index=False)
            print(f"Saved results to {OUTPUT_FILE}")
            print(df)
            
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    run_test()
