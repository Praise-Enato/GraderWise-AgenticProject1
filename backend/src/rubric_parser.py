from typing import List
from fastapi import UploadFile
import os
from langchain_core.prompts import ChatPromptTemplate
from backend.src.models import RubricItem
from backend.src import rag
from backend.src.llm import get_llm
import json

# WORKAROUND: Remove NO_PROXY if it causes DNS issues
if "NO_PROXY" in os.environ:
    if "api.deepseek.com" not in os.environ.get("NO_PROXY", ""):
        del os.environ["NO_PROXY"]

# The LLM is obtained lazily from the model router (get_llm("rubric")) inside
# parse_rubric, so a missing API key fails at call time with a clear message
# rather than at import time.

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
    - developing_points: The points awarded for partial or developing mastery (if specified).
    - developing_description: Description of what constitutes partial or developing mastery.
    - zero_points: The points awarded for failure or missing criteria (usually 0).
    - zero_description: Description of what constitutes zero points.
    
    Rules:
    - If the input is a table, map the columns intelligent to Criteria, Points, and Description.
    - If points are given as a range (e.g., "0-10"), use the max value.
    - If no points are specified, infer reasonable weights or assign 0.
    - Extract descriptions for partial/developing and zero points if available in the text/table.
    
    Output strictly in JSON format matching the following structure:
    Example:
    {{
        "items": [
            {{
                "criteria": "Thesis", 
                "max_points": 10, 
                "description": "Clear thesis statement.",
                "developing_points": 5,
                "developing_description": "Thesis is present but vague.",
                "zero_points": 0,
                "zero_description": "No thesis statement."
            }},
            {{
                "criteria": "Grammar", 
                "max_points": 5,  
                "description": "No errors.",
                "developing_points": 2.5,
                "developing_description": "Some errors but readable.",
                "zero_points": 0,
                "zero_description": "Unreadable due to errors."
            }}
        ]
    }}
    """
    
    # Pass the rubric content as a template VARIABLE, not interpolated into the
    # template string — otherwise any '{' or '}' in the rubric is parsed as a
    # template field and crashes /parse-rubric.
    human_prompt = "RUBRIC CONTENT:\n{content}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    
    # Bind JSON mode. Model comes from the router (get_llm) so config lives in one place.
    json_llm = get_llm("rubric").bind(response_format={"type": "json_object"})
    chain = prompt | json_llm
    
    try:
        response = chain.invoke({"content": aggregated_text})
        content = response.content.strip()
        
        # --- FIX: Handle Markdown Code Blocks ---
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        
        if content.endswith("```"):
            content = content[:-3]
            
        content = content.strip()
        # --------------------------------------

        parsed_data = json.loads(content)
        items = [RubricItem(**item) for item in parsed_data.get("items", [])]
        return items
    except Exception as e:
        print(f"Error parsing rubric with LLM: {e}")
        # Return detailed error for debugging
        raise ValueError(f"Failed to parse rubric structure. Error: {str(e)}")