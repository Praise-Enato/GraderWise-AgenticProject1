
import os
import json
import pandas as pd
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# Setup
load_dotenv() # Load env vars including GROQ_API_KEY
# os.environ["GROQ_API_KEY"] = ... # Removed hardcoded key attempt
# Note: In a real script we should load from env, but for this standalone script we assume env is set or we use the one from main.
# To be safe, let's try to load from .env or just assume the user has it set in their shell or we can copy it from main.py if we knew it.
# For now, assuming the environment has the key or I will use the one I saw in logs or just rely on global env.
# Actually, I'll allow it to fail if missing, but let's try to be robust. 
# Best practice: relying on os.environ.

RUBRIC = json.dumps([
    {
        "criteria": "Historical Accuracy", 
        "max_points": 4, 
        "description": "Accuracy of facts regarding World War II."
    },
    {
        "criteria": "Argument & Quality", 
        "max_points": 4, 
        "description": "Quality of writing, structure, and persuasion."
    },
    {
        "criteria": "Relevance", 
        "max_points": 2, 
        "description": "Relevance to the prompt: 'Discuss the impact of World War II'."
    }
])

def generate_essays():
    print("Initializing Llama 3 Generator...")
    try:
        llm = ChatGroq(model_name="llama-3.1-8b-instant")
    except Exception as e:
        print(f"Error initializing ChatGroq: {e}")
        return

    essays = []
    
    # 1. The Hallucinator
    print("Generating: The Hallucinator...")
    hallucinator_prompt = "Write a persuasive, grammatically perfect essay about World War II, but centrally claim that Napoleon Bonaparte was a key general fighting for the Allies in 1944. Make it sound very convincing."
    hallucinator_text = llm.invoke(hallucinator_prompt).content
    essays.append({"student_id": "hallucinator", "type": "The Hallucinator", "text": hallucinator_text, "rubric": RUBRIC})

    # 2. The Sloppy Genius
    print("Generating: The Sloppy Genius...")
    sloppy_prompt = "Write a short essay about the Battle of Stalingrad. It must be factually 100% correct and insightful, BUT write it with terrible spelling, no punctuation, slang (like 'fr' 'no cap'), and all lowercase."
    sloppy_text = llm.invoke(sloppy_prompt).content
    essays.append({"student_id": "sloppy_genius", "type": "The Sloppy Genius", "text": sloppy_text, "rubric": RUBRIC})

    # 3. The Cheat (Pizza)
    print("Generating: The Cheat...")
    cheat_text = "Pizza is a savory dish of Italian origin consisting of a usually round, flattened base of leavened wheat-based dough topped with tomatoes, cheese, and often various other ingredients, which is then baked at a high temperature, traditionally in a wood-fired oven. A small pizza is sometimes called a pizzetta. A person who makes pizza is known as a pizzaiolo."
    essays.append({"student_id": "cheat", "type": "The Cheat", "text": cheat_text, "rubric": RUBRIC})

    # 4. The Model Student
    print("Generating: The Model Student...")
    model_prompt = "Write a perfect, concise, well-structured academic essay about the impact of World War II on global geopolitics. Ensure 100% accuracy."
    model_text = llm.invoke(model_prompt).content
    essays.append({"student_id": "model_student", "type": "The Model Student", "text": model_text, "rubric": RUBRIC})

    # Save
    df = pd.DataFrame(essays)
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'synthetic_benchmarks.csv')
    df.to_csv(output_path, index=False)
    print(f"Synthetic benchmarks saved to {output_path}")

if __name__ == "__main__":
    generate_essays()
