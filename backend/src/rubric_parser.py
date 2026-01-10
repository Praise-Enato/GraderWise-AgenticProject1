from typing import List
from fastapi import UploadFile
from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from backend.src.models import RubricItem
from backend.src import rag
import json

# WORKAROUND: Remove NO_PROXY if it causes DNS issues
if "NO_PROXY" in os.environ:
    if "api.deepseek.com" not in os.environ.get("NO_PROXY", ""):
        # print(f"DEBUG: Removing NO_PROXY to fix DNS...")
        del os.environ["NO_PROXY"]

# Initialize LLM (DeepSeek-V3)
api_key = os.getenv("DEEPSEEK_API_KEY")

llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=api_key,
    openai_api_base="https://api.deepseek.com",
    temperature=0
)

def parse_rubric(files: List[UploadFile]) -> List[RubricItem]:
    """
    Parses uploaded files (Rubric) into structured RubricItems using an LLM.
    Supports PDF, DOCX, TXT, CSV, XLSX.
    """
    aggregated_text = ""
    
    for file in files:
        try:
            text = rag.extract_text_from_file(file)
            aggregated_text += f"\n--- File: {file.filename} ---\n{text}\n"
        except Exception as e:
            print(f"Error extracting text from {file.filename}: {e}")

    if not aggregated_text.strip():
        raise ValueError("No text could be extracted from the uploaded files.")

    # LLM Extraction Logic
    system_prompt = """You are an expert Rubric Creator and Data Parser.
    Your task is to extract a structured Grading Rubric from the provided raw text or markdown table.
    
    The input may be:
    - A standard text rubric.
    - A markdown table (converted from CSV/Excel).
    
    Target Structure:
    - criteria: The name of the category (e.g., "Thesis", "Grammar", "Analysis").
    - max_points: The maximum score for this category (integer).
    - description: A concise description of what is required for full points.
    
    Rules:
    - If the input is a table, map the columns intelligent to Criteria, Points, and Description.
    - If points are given as a range (e.g., "0-10"), use the max value.
    - If no points are specified, infer reasonable weights or assign 0.
    
    Output strictly in JSON format matching the following structure:
    Example:
    {{
        "items": [
            {{"criteria": "Thesis", "max_points": 10, "description": "Clear thesis statement."}},
            {{"criteria": "Grammar", "max_points": 5,  "description": "No errors."}}
        ]
    }}
    """
    
    human_prompt = f"RUBRIC CONTENT:\n{aggregated_text}"
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    
    # Bind JSON mode
    json_llm = llm.bind(response_format={"type": "json_object"})
    chain = prompt | json_llm
    
    try:
        response = chain.invoke({})
        parsed_data = json.loads(response.content)
        items = [RubricItem(**item) for item in parsed_data.get("items", [])]
        return items
    except Exception as e:
        print(f"Error parsing rubric with LLM: {e}")
        # Return detailed error for debugging
        raise ValueError(f"Failed to parse rubric structure. Error: {str(e)}")
