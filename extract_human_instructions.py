import os
import sys
import asyncio

# Setup environment for Langchain
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
from backend.src import agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader

async def extract_and_summarize():
    pdf_path = "backend/business plan human graders instructions/Africa Business Plan Competition Handbook Final.pdf"
    docx_path = "backend/business plan human graders instructions/Judging Instructions- BYUMS Africa BPC 2026.docx"
    
    # 1. Extract PDF
    print("Extracting PDF...")
    pdf_text = ""
    try:
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        pdf_text = "\n".join([d.page_content for d in docs])
    except Exception as e:
        print("Error extracting PDF:", e)
        
    # 2. Extract DOCX
    print("Extracting DOCX...")
    docx_text = ""
    try:
        loader = Docx2txtLoader(docx_path)
        docs = loader.load()
        docx_text = "\n".join([d.page_content for d in docs])
    except Exception as e:
        print("Error extracting DOCX:", e)
        
    # The handbook is large, so let's only take the first ~15,000 characters which usually contain the rules
    total_text = f"--- AFRICA BUSINESS PLAN COMPETITION HANDBOOK ---\n{pdf_text[:15000]}\n\n--- JUDGING INSTRUCTIONS ---\n{docx_text}"
    
    print(f"Total extracted characters to summarize: {len(total_text)}")
    
    # 3. Summarize with LLM
    print("Asking LLM to extract necessary instructions...")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert business plan evaluator. Extract the most important grading guidelines, standards, and judging instructions from the provided text. Focus heavily on how to assign points, what constitutes a good vs bad business plan, and any specific requirements. Return the result as a detailed Markdown document. Do not include unnecessary fluff or general handbook rules that don't apply to grading."),
        ("user", "{text}")
    ])
    
    chain = prompt | agent.llm | StrOutputParser()
    summary = await chain.ainvoke({"text": total_text})
    
    # 4. Save to a new document
    out_path = "backend/training_data/human_grader_instructions_summary.md"
    with open(out_path, "w") as f:
        f.write(summary)
        
    print(f"Saved summarized instructions to {out_path}")

if __name__ == "__main__":
    asyncio.run(extract_and_summarize())
