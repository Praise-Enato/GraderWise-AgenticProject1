# Business Plan Grading System Implementation Plan

## Context

GradeWise currently supports academic grading (essays, assignments, exams) using a 4-node LangGraph agentic workflow with DeepSeek-V3 and RAG-based context retrieval. This plan adds a **business plan grading system** as a completely separate workflow that can grade:

- **Business plan slide decks** (PPTX format)
- **Business plan documents** (PDF/DOCX)
- **Mixed business plan types** (startup pitches, MBA-style plans, enterprise proposals, nonprofit plans)

**Why this change?** Business plan evaluation requires different criteria than academic grading:
- Evaluates **market feasibility** vs factual correctness
- Requires **financial viability analysis** vs knowledge demonstration
- Needs **industry benchmark context** vs course material context
- Demands **investor/mentor feedback style** vs academic tutor style

**Architecture Strategy:** Dual-workflow approach with conditional routing at entry point. This guarantees **zero impact** on existing academic grading while enabling business-specific evaluation logic.

**User Requirements:**
- Text-only PPTX processing initially (Phase 1), vision capabilities later
- Support mixed business plan types (flexible rubric templates)
- Use pre-loaded starter pack for business context (Y Combinator guides, financial templates)
- Budget: Flexible up to $5/month for ~100 submissions
- Phased implementation for incremental value delivery

---

## Architecture Overview

### Current System
```
Entry → retrieve → grade_submission → validate_grade ⇄ (retry loop) → generate_feedback → END
```

### Proposed System
```
Entry → route_grading_type → [academic_workflow | business_workflow]
                                      ↓
                         business_retrieve → process_pptx → grade_business_plan
                         → validate_business_grade ⇄ (retry loop)
                         → generate_business_feedback → END
```

**Key Innovation:**
- Add `grading_type` field to `AgentState` ("academic" | "business_plan")
- Create separate business workflow graph
- Use conditional routing function to branch based on grading type
- Academic workflow remains completely untouched

---

## Critical Files to Modify/Create

### Files to Modify

1. **[backend/src/agent.py](backend/src/agent.py)** (Lines 60-73, 77+)
   - Add `grading_type: str` field to `AgentState` TypedDict
   - Add `pptx_content: List[dict]` for processed PPTX slides
   - Add `business_context_type: str` ("startup" | "enterprise" | "nonprofit")
   - Create `route_grading_type()` conditional function
   - Implement router at entry point

2. **[backend/src/models.py](backend/src/models.py)** (End of file)
   - Add `BusinessPlanGradeRequest` Pydantic model
   - Add `PPTXMetadata` model for slide extraction results

3. **[backend/src/main.py](backend/src/main.py)** (After line 111)
   - Add `/grade-business-plan` endpoint
   - Add `/extract-pptx` endpoint
   - Add `/ingest-business-context` endpoint

### New Files to Create

4. **backend/src/pptx_processor.py** (NEW)
   - `PPTXProcessor` class for text extraction
   - `extract_text_only()` method using python-pptx
   - `to_markdown()` method for formatting
   - Metadata detection (slide count, charts, images)

5. **backend/src/business_agent.py** (NEW)
   - Business-specific workflow nodes
   - `grade_business_plan()` node with business rubric logic
   - `validate_business_grade()` with business-specific validation
   - `generate_business_feedback()` with investor/mentor tone
   - Business workflow graph construction

6. **backend/src/business_rag.py** (NEW)
   - Separate ChromaDB collection for business context
   - `ingest_business_context()` for templates/guides
   - `retrieve_business_context()` with business_type filtering
   - Pre-load recommended starter pack

7. **backend/src/business_rubric_templates.py** (NEW)
   - Template rubrics for different business types
   - Startup pitch deck rubric (problem, market, model, financials, team)
   - Enterprise business plan rubric (strategy, operations, financials)
   - Nonprofit proposal rubric (impact, sustainability, budget)

---

## Implementation Phases

### **Phase 1: Foundation - Text-Only PPTX Business Grading** (Week 1-2)

**Goal:** MVP that can grade business plans with PPTX text extraction and business-specific rubric.

#### Tasks

1. **Install Dependencies**
   - Add `markitdown[all]` to `requirements.txt`
   - Run `pip install markitdown[all]`

2. **Create PPTX Processor** ([backend/src/pptx_processor.py](backend/src/pptx_processor.py))
   ```python
   from markitdown import MarkItDown
   from typing import Dict, List
   import os

   class PPTXProcessor:
       def __init__(self):
           # Initialize MarkItDown converter
           self.converter = MarkItDown()

       def extract_to_markdown(self, pptx_path: str) -> Dict:
           """
           Extract PPTX to markdown using Microsoft MarkItDown.
           Preserves structure: tables, lists, headers, formatting.

           Returns:
           {
               "markdown_content": str,  # Full markdown text
               "slide_count": int,       # Number of slides
               "has_tables": bool,       # Contains tables
               "has_images": bool,       # Contains images
               "text_length": int        # Character count
           }
           """
           # Convert PPTX to markdown
           result = self.converter.convert(pptx_path)
           markdown_text = result.text_content

           # Analyze content
           slide_count = markdown_text.count("## Slide") or markdown_text.count("##")
           has_tables = "|" in markdown_text and "---" in markdown_text
           has_images = "![" in markdown_text or "[image]" in markdown_text.lower()
           text_length = len(markdown_text)

           return {
               "markdown_content": markdown_text,
               "slide_count": slide_count,
               "has_tables": has_tables,
               "has_images": has_images,
               "text_length": text_length,
               "structure_preserved": True  # MarkItDown preserves structure
           }
   ```

3. **Update Data Models** ([backend/src/models.py](backend/src/models.py))
   ```python
   class PPTXFile(BaseModel):
       filename: str
       markdown_content: str
       slide_count: int
       has_visuals: bool

   class BusinessPlanGradeRequest(BaseModel):
       pptx_files: Optional[List[UploadFile]] = None
       document_files: Optional[List[SubmissionFile]] = None
       rubric: List[RubricItem]
       student_id: str
       business_context_type: str = "startup"  # startup|enterprise|nonprofit
       grading_type: str = "business_plan"
   ```

**Why Microsoft MarkItDown?**
   - Official Microsoft open-source tool designed for LLM pipelines
   - Automatically preserves tables, lists, headers, and formatting
   - Pure Python (no subprocess overhead)
   - Simple API, well-maintained
   - Bonus: Future integration with OpenAI for image descriptions (Phase 4)

4. **Create Business Rubric Templates** ([backend/src/business_rubric_templates.py](backend/src/business_rubric_templates.py))
   ```python
   STARTUP_RUBRIC = [
       RubricItem(
           criteria="Problem Statement",
           max_points=15,
           description="Clear customer pain point with market evidence",
           developing_description="Problem identified but lacks specificity",
           zero_description="Vague or missing problem statement"
       ),
       RubricItem(
           criteria="Market Opportunity (TAM/SAM/SOM)",
           max_points=15,
           description="Market sizing with credible sources and methodology",
           ...
       ),
       RubricItem(
           criteria="Business Model & Unit Economics",
           max_points=15,
           description="Clear revenue model with CAC, LTV, margins",
           ...
       ),
       RubricItem(
           criteria="Financial Projections (3-5 year)",
           max_points=20,
           description="Realistic projections with P&L, cash flow, assumptions",
           ...
       ),
       RubricItem(
           criteria="Competitive Analysis",
           max_points=10,
           description="Identifies competitors, clear differentiation, defensible moat",
           ...
       ),
       RubricItem(
           criteria="Team & Execution Capability",
           max_points=10,
           description="Relevant experience, complementary skills, track record",
           ...
       ),
       RubricItem(
           criteria="Presentation Quality (Pitch Deck)",
           max_points=15,
           description="Professional design, clear visuals, compelling narrative",
           ...
       )
   ]

   # Similar templates for ENTERPRISE_RUBRIC, NONPROFIT_RUBRIC

   def get_rubric_template(business_type: str) -> List[RubricItem]:
       templates = {
           "startup": STARTUP_RUBRIC,
           "enterprise": ENTERPRISE_RUBRIC,
           "nonprofit": NONPROFIT_RUBRIC
       }
       return templates.get(business_type, STARTUP_RUBRIC)
   ```

5. **Create Business Agent Workflow** ([backend/src/business_agent.py](backend/src/business_agent.py))
   ```python
   from langgraph.graph import StateGraph, END
   from backend.src.agent import AgentState, llm
   from backend.src.models import GradeResult

   # Business-specific grading prompt
   BUSINESS_GRADER_PROMPT = """You are a Senior Venture Capital Partner evaluating a business plan.

   EVALUATION PRINCIPLES:
   1. Market Realism: Validate market size against industry benchmarks
   2. Financial Feasibility: Check if projections align with typical growth rates
   3. Competitive Awareness: Assess if analysis acknowledges obvious competitors
   4. Team Credibility: Evaluate relevant experience for execution
   5. Presentation Quality: Judge if deck is investor-ready

   SCORING RULES:
   - For Financial Projections: Flag if >100% MoM growth sustained >6 months
   - For Market Opportunity: Verify TAM/SAM/SOM sources and assumptions
   - For Business Model: Require CAC, LTV, and margin definitions

   Return JSON with assessments per criteria.
   """

   def grade_business_plan(state: AgentState) -> dict:
       """Grade business plan using business-specific rubric logic"""
       # Similar to grade_submission but with BUSINESS_GRADER_PROMPT
       # Process PPTX content + document content together
       # Return: {"grade_data", "thinking_process"}

   def validate_business_grade(state: AgentState) -> dict:
       """Validate with business-specific rules"""
       # Check standard validations (score bounds, consistency)
       # Add business-specific checks:
       #   - Financial realism (growth rates)
       #   - Market size sanity (min $10M TAM)
       #   - Completeness (problem, market, model, financials)
       # Return: {"is_valid", "grader_feedback", "revision_number"}

   def generate_business_feedback(state: AgentState) -> dict:
       """Generate investor/mentor-style feedback"""
       # Tone: Business mentor (not academic tutor)
       # Format: Executive Summary + Critical Gaps + Investor Perspective + Strengths
       # Use emoji: 🎯 🚀 ⚠️ 💡
       # Return: {"final_feedback", "grade_result"}

   # Build business workflow graph
   business_workflow = StateGraph(AgentState)
   business_workflow.add_node("grade_business_plan", grade_business_plan)
   business_workflow.add_node("validate_business_grade", validate_business_grade)
   business_workflow.add_node("generate_business_feedback", generate_business_feedback)
   business_workflow.set_entry_point("grade_business_plan")
   # Add conditional edges for retry loop (max 3 attempts)
   business_app = business_workflow.compile()
   ```

6. **Update Agent Router** ([backend/src/agent.py](backend/src/agent.py))
   ```python
   # Update AgentState (line 60)
   class AgentState(TypedDict):
       # ... existing fields ...
       grading_type: str  # "academic" | "business_plan"
       pptx_content: List[dict]  # Processed PPTX slides
       business_context_type: str  # "startup" | "enterprise" | "nonprofit"

   # Create router function (after node implementations)
   def route_grading_type(state: AgentState) -> str:
       """Route to appropriate workflow based on grading type"""
       grading_type = state.get("grading_type", "academic")
       if grading_type == "business_plan":
           return "business"
       return "academic"

   # Build main router graph (at end of file)
   from backend.src import business_agent

   main_workflow = StateGraph(AgentState)
   main_workflow.add_node("academic", app)  # Existing academic workflow
   main_workflow.add_node("business", business_agent.business_app)
   main_workflow.add_conditional_edges(
       START,
       route_grading_type,
       {"academic": "academic", "business": "business"}
   )
   router_app = main_workflow.compile()

   # Export router_app as main interface
   ```

7. **Add API Endpoints** ([backend/src/main.py](backend/src/main.py))
   ```python
   from backend.src.pptx_processor import PPTXProcessor
   from backend.src.business_rubric_templates import get_rubric_template

   @app.post("/extract-pptx")
   async def extract_pptx_endpoint(file: UploadFile = File(...)):
       """Extract markdown from PPTX file using Microsoft MarkItDown"""
       try:
           # Save temp file
           temp_path = f"./backend/data/temp_uploads/{file.filename}"
           os.makedirs("./backend/data/temp_uploads", exist_ok=True)
           with open(temp_path, "wb") as f:
               f.write(await file.read())

           # Extract using MarkItDown
           processor = PPTXProcessor()
           result = processor.extract_to_markdown(temp_path)

           # Cleanup
           os.remove(temp_path)

           return result
       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))

   @app.post("/grade-business-plan", response_model=GradeResult)
   async def grade_business_plan_endpoint(request: BusinessPlanGradeRequest):
       """Grade business plan with PPTX + document"""
       try:
           # Process PPTX files using MarkItDown
           pptx_content = []
           if request.pptx_files:
               processor = PPTXProcessor()
               for pptx in request.pptx_files:
                   # Save temp file
                   temp_path = f"./backend/data/temp_uploads/{pptx.filename}"
                   with open(temp_path, "wb") as f:
                       f.write(await pptx.read())

                   # Extract markdown
                   result = processor.extract_to_markdown(temp_path)
                   pptx_content.append({
                       "filename": pptx.filename,
                       "content": result["markdown_content"]
                   })

                   # Cleanup
                   os.remove(temp_path)

           # Prepare document files
           doc_files = [f.dict() for f in request.document_files] if request.document_files else []

           # Combine PPTX + documents
           all_files = pptx_content + doc_files

           # Invoke business workflow
           inputs = {
               "submission_files": all_files,
               "rubric": request.rubric,
               "grading_type": "business_plan",
               "business_context_type": request.business_context_type,
               "context": [],
               "grade_result": None
           }

           result = await run_in_threadpool(agent.router_app.invoke, inputs)
           return result["grade_result"]
       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))

   @app.get("/business-rubric-template/{business_type}")
   async def get_business_rubric_template(business_type: str):
       """Get rubric template for business type"""
       return get_rubric_template(business_type)
   ```

#### Success Criteria
- ✅ Can extract markdown from PPTX files with preserved structure (tables, lists, headers)
- ✅ MarkItDown successfully converts PPTX to well-formatted markdown
- ✅ Detects presence of tables/images in markdown output
- ✅ Business plan grading returns score + feedback
- ✅ Feedback tone is business/investor-focused (not academic)
- ✅ Academic grading still works identically (no regression)
- ✅ Cost: ~$0.003-0.008 per submission

**Estimated Effort:** 12-16 hours

---

### **Phase 2: Business RAG Context System** (Week 3)

**Goal:** Add industry benchmarks and business templates for context-aware grading.

#### Tasks

1. **Create Business RAG Module** ([backend/src/business_rag.py](backend/src/business_rag.py))
   ```python
   from langchain_chroma import Chroma
   from backend.src.rag import get_embedding_function, extract_text_from_file

   BUSINESS_CHROMA_PATH = "./backend/data/chroma_business"

   class BusinessRAG:
       @staticmethod
       def ingest_business_context(files: List[UploadFile], context_type: str):
           """Ingest business context (templates, guides, benchmarks)"""
           # Similar to rag.ingest_documents but:
           # - Uses BUSINESS_CHROMA_PATH
           # - Tags documents with context_type metadata
           # - Smaller chunk size (500 chars vs 1000 for faster retrieval)

       @staticmethod
       def retrieve_business_context(query: str, context_type: str = "startup", k: int = 5) -> List[str]:
           """Retrieve business context filtered by type"""
           # Query with metadata filter: {"context_type": context_type}
           # Return fewer chunks (5 vs 10 for academic)
   ```

2. **Pre-load Starter Pack**
   - Create `backend/data/business_context/` directory
   - Download/prepare starter materials:
     - Y Combinator Startup School guides (public PDFs)
     - Financial ratios guide (Investopedia content)
     - Standard pitch deck structure template
     - Unit economics definitions (CAC, LTV, ARR, MRR)
   - Script to auto-ingest on first run

3. **Update Business Agent** ([backend/src/business_agent.py](backend/src/business_agent.py))
   - Add `business_retrieve()` node before grading
   - Query RAG with rubric criteria (e.g., "market sizing methodology, financial projection benchmarks")
   - Pass context to grading prompt

4. **Add Endpoint** ([backend/src/main.py](backend/src/main.py))
   ```python
   @app.post("/ingest-business-context")
   async def ingest_business_context_endpoint(
       files: List[UploadFile] = File(...),
       context_type: str = "startup"
   ):
       """Ingest business-specific context materials"""
       try:
           count = BusinessRAG.ingest_business_context(files, context_type)
           return {"status": "success", "files_processed": count}
       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))
   ```

#### Success Criteria
- ✅ Business context stored in separate ChromaDB collection
- ✅ Grading feedback cites industry benchmarks (e.g., "Typical SaaS CAC:LTV is 3:1")
- ✅ Market size validation references standard methodologies
- ✅ Starter pack auto-loads on system initialization

**Estimated Effort:** 8-10 hours

---

### **Phase 3: Quick Demo Frontend Integration** (Week 3)

**Goal:** Create minimal frontend UI for supervisor demo before completing all backend features.

#### Tasks

1. **Add Grader Type Selector to Dashboard** ([frontend/app/(dashboard)/dashboard/page.tsx](frontend/app/(dashboard)/dashboard/page.tsx))
   - Add dropdown/select component for grader type selection
   - Options: "Academic Grader" (existing) or "Business Plan Grader" (new)
   - Store selection in state

2. **Create Grader Setup Section**
   - Upload rubric component (use existing from grading page)
   - Upload context materials (optional)
   - Display selected files with preview
   - "Start Grading Job" button

3. **Update Navigation Flow**
   - When "Start Grading Job" clicked:
     - Store grader type + rubric + context in localStorage
     - Navigate to `/grading` page with query param `?type=business` or `?type=academic`

4. **Modify Grading Page** ([frontend/app/(dashboard)/grading/page.tsx](frontend/app/(dashboard)/grading/page.tsx))
   - Read `type` query parameter from URL
   - If `type=business`:
     - Show "Business Plan Grading" title
     - Show PPTX upload section (new)
     - Show document upload section (PDF/DOCX)
     - Load business rubric from localStorage
   - If `type=academic` or no type:
     - Keep existing academic grading UI

5. **Add Business Plan Grading Logic**
   - Update submit handler to call `/grade-business-plan` endpoint when type is business
   - Display results with business-specific formatting (investor feedback tone)
   - Show PPTX metadata (slide count, has_tables, has_images)

6. **Create PPTX Upload Component** ([frontend/components/PPTXUpload.tsx](frontend/components/PPTXUpload.tsx))
   ```typescript
   export function PPTXUpload({ onUpload }: { onUpload: (files: File[]) => void }) {
     // Drag-and-drop or file input for PPTX files
     // Display uploaded PPTX files with slide count preview
     // Accept: .pptx files only
   }
   ```

7. **Update API Client** ([frontend/lib/api.ts](frontend/lib/api.ts))
   ```typescript
   export async function extractPPTX(file: File): Promise<PPTXMetadata> {
     // POST to /extract-pptx
   }

   export async function gradeBusinessPlan(data: BusinessPlanGradeData): Promise<GradeResult> {
     // POST to /grade-business-plan
   }
   ```

#### UI Flow for Demo

```
Dashboard Page
  └─ [Dropdown] Select Grader Type
       ├─ Academic Grader (default)
       └─ Business Plan Grader (new)
  └─ [File Upload] Upload Rubric (optional, can use template)
  └─ [File Upload] Upload Context (optional)
  └─ [Button] Start Grading Job
       ↓
Grading Page (?type=business)
  └─ Title: "Business Plan Grading"
  └─ [PPTX Upload] Upload pitch deck
  └─ [Document Upload] Upload business plan document (PDF/DOCX)
  └─ [Rubric Editor] Edit/view rubric (pre-loaded from dashboard)
  └─ [Button] Grade Submission
       ↓
Results Display
  └─ Score: 85/100
  └─ Feedback: [Investor-style feedback with 🎯 🚀 ⚠️ 💡]
  └─ PPTX Info: "15 slides analyzed, 3 tables detected"
```

#### Success Criteria
- ✅ Can select "Business Plan Grader" from dashboard
- ✅ Can upload PPTX + PDF files for grading
- ✅ Grading returns business-specific feedback
- ✅ UI clearly distinguishes business vs academic grading
- ✅ Demo-ready for supervisor presentation
- ✅ Academic grading flow unchanged

**Estimated Effort:** 6-8 hours

---

### **Phase 4: Enhanced PPTX Metadata & Chart Detection** (Week 4)

**Goal:** Add visual element detection and placeholder annotations for future vision integration.

#### Tasks

1. **Enhance PPTX Processor** ([backend/src/pptx_processor.py](backend/src/pptx_processor.py))
   - Analyze markdown output for chart indicators
   - Parse table structures from markdown
   - Count images in markdown (`![image]` tags)
   - Calculate visual density score based on image/table count
   - Flag "chart-heavy" decks (>50% slides with images/tables)

2. **Update Grading Logic** ([backend/src/business_agent.py](backend/src/business_agent.py))
   - Adjust Presentation Quality scoring based on metadata
   - Add note in feedback: "Slide X contains financial chart [visual analysis pending]"
   - Provide partial credit for charts even without vision analysis

#### Success Criteria
- ✅ System identifies decks with heavy visual content
- ✅ Feedback acknowledges chart presence specifically
- ✅ Rubric scores account for presentation quality metadata

**Estimated Effort:** 6-8 hours

---

### **Phase 5 (Optional): Vision Model Integration** (Week 5-6)

**Goal:** Add multimodal vision analysis for slides with charts/diagrams.

#### Tasks

1. **Integrate Gemini 2.0 Flash**
   - Add `google-generativeai` to requirements.txt
   - Add `GOOGLE_API_KEY` to environment variables
   - Create vision analyzer module

2. **Selective Vision Processing**
   - Only process decks flagged as "chart-heavy" in Phase 3
   - Convert slides to images (pptx → PDF → PNG)
   - Send to Gemini 2.0 Flash with prompt: "Describe this chart/diagram"

3. **Integrate Visual Analysis into Grading**
   - Add visual analysis results to grading context
   - Update Presentation Quality criteria to evaluate design
   - Provide specific feedback on chart accuracy/clarity

#### Success Criteria
- ✅ Can analyze and describe charts accurately
- ✅ Evaluates slide design quality
- ✅ Cost remains under $5/month for 100 submissions

**Estimated Effort:** 12-16 hours (Optional - only if vision is needed)

---

### **Phase 6: Full Frontend Integration & Polish** (Week 7)

**Goal:** Complete full-featured business plan grading UI with dedicated route and polish.

#### Tasks

1. **Create Business Grading Route** ([frontend/app/(dashboard)/business-grading/page.tsx](frontend/app/(dashboard)/business-grading/page.tsx))
   - PPTX upload component (drag-and-drop)
   - Document upload (PDF/DOCX)
   - Business type selector (startup/enterprise/nonprofit)
   - Rubric template selector with preview
   - Submit and view results

2. **Update API Client** ([frontend/lib/api.ts](frontend/lib/api.ts))
   ```typescript
   export async function gradeBusinessPlan(data: {
     pptxFiles: File[];
     documentFiles: File[];
     rubric: RubricItem[];
     studentId: string;
     businessType: string;
   }): Promise<GradeResult> {
     // POST to /grade-business-plan
   }
   ```

3. **Add Navigation** ([frontend/app/(dashboard)/Sidebar.tsx](frontend/app/(dashboard)/Sidebar.tsx))
   - Add "Business Plan Grading" menu item
   - Icon: Briefcase or PresentationChart

4. **Results Display**
   - Show PPTX summary (slide count, visual elements detected)
   - Display business-specific feedback formatting
   - Highlight investment decision / funding readiness

#### Success Criteria
- ✅ Can upload PPTX + PDF via UI
- ✅ Business rubric templates load automatically
- ✅ Results display investor-focused feedback
- ✅ Academic grading page unchanged

**Estimated Effort:** 10-12 hours

---

### **Phase 7: Testing & Optimization** (Week 8)

**Goal:** Validate quality and cost-effectiveness.

#### Tasks

1. **Create Test Suite**
   - 10 sample business plans (3 startup, 3 enterprise, 2 nonprofit, 2 edge cases)
   - Human expert grades as ground truth
   - Automated regression tests

2. **Performance Benchmarking**
   - Measure correlation with human graders (target: >0.75)
   - Track grading time per submission
   - Monitor token usage and costs

3. **Cost Optimization**
   - Implement prompt compression
   - Optimize RAG chunk retrieval (reduce from 10→5 chunks)
   - Add token usage logging

4. **Error Handling**
   - Handle malformed PPTX files gracefully
   - Fallback for extraction failures
   - Retry logic for API timeouts

#### Success Criteria
- ✅ >0.75 correlation with human expert grades
- ✅ <$0.02 average cost per submission
- ✅ <30 second grading time (end-to-end)
- ✅ Zero crashes on edge cases

**Estimated Effort:** 8-10 hours

---

## Cost Analysis

### Phase 1-3 (Text-Only)
**Per Submission:**
- PPTX Text (3,000 tokens) + Document (5,000 tokens) + Rubric (1,500 tokens) + Context (0) = 9,500 input tokens
- Grading Output (2,000 tokens) + Feedback (1,500 tokens) = 3,500 output tokens
- **Cost with DeepSeek-V3:** $0.0026 (input) + $0.0039 (output) = **$0.0065 per submission**

**Monthly (100 submissions):** $0.65

### Phase 2 (With Business RAG)
**Additional Cost:**
- RAG Context (2,000 tokens) = $0.0005
- **Total per submission:** **$0.0070**

**Monthly (100 submissions):** $0.70

### Phase 4 (With Vision - Optional)
**Additional Cost (30% of submissions):**
- Vision analysis (60,000 tokens Gemini 2.0 Flash) = $0.0045 (input) + $0.0018 (output) = $0.0063
- **Average per submission:** $0.0070 + ($0.0063 × 0.3) = **$0.0089**

**Monthly (100 submissions):** $0.89

**Budget Status:** Well within $5/month target (85% under budget)

---

## Verification Plan

### After Phase 1
1. Test PPTX extraction with sample pitch deck
   ```bash
   curl -X POST http://localhost:8000/extract-pptx \
     -F "file=@sample_pitch.pptx"
   ```
2. Grade sample business plan
   ```bash
   curl -X POST http://localhost:8000/grade-business-plan \
     -H "Content-Type: application/json" \
     -d '{
       "pptx_files": [...],
       "document_files": [...],
       "rubric": [...],
       "student_id": "test_001",
       "business_context_type": "startup"
     }'
   ```
3. Verify academic grading still works
   ```bash
   curl -X POST http://localhost:8000/grade \
     -H "Content-Type: application/json" \
     -d '{...existing academic request...}'
   ```

### After Phase 2
1. Ingest business context
   ```bash
   curl -X POST http://localhost:8000/ingest-business-context \
     -F "files=@yc_guide.pdf" \
     -F "context_type=startup"
   ```
2. Verify feedback cites industry benchmarks
3. Check ChromaDB has separate collections (chroma/ vs chroma_business/)

### After Phase 3 (Quick Demo)
1. Navigate to dashboard
2. Select "Business Plan Grader" from dropdown
3. Upload business rubric (or use template)
4. Click "Start Grading Job"
5. Upload sample PPTX + PDF business plan
6. Click "Grade" and verify results display

### After Phase 6 (Full Frontend)
1. Navigate to `/business-grading` in browser
2. Upload PPTX + PDF
3. Select "Startup" business type
4. Submit and verify results display correctly
5. Check academic grading page still works at `/grading`

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| PPTX parsing failures | High | Robust error handling, detailed error messages, fallback to manual upload |
| Academic workflow regression | **CRITICAL** | Comprehensive regression tests, separate code paths, conditional routing verification |
| Cost overruns | Medium | Token counting, budget alerts at $3/month threshold, hybrid vision approach |
| Poor business grading quality | High | Human validation with 10 test cases, iterative prompt refinement, expert review |
| Context hallucinations | Medium | Confidence scoring, cross-reference with multiple sources, citation requirements |

---

## Dependencies

### New Python Packages
```
markitdown[all]                  # Microsoft MarkItDown for PPTX→Markdown (Phase 1)
google-generativeai>=0.8.0       # Gemini API (Phase 4, optional)
```

### Environment Variables
```env
DEEPSEEK_API_KEY=sk-...          # Existing
GOOGLE_API_KEY=AIza...           # Phase 4 only (optional)
```

### System Requirements
- Python 3.10+
- 500MB additional disk space for business context ChromaDB
- LibreOffice (optional, Phase 4 fallback)

---

## Summary

This plan implements business plan grading as a **separate, parallel workflow** that:
1. **Preserves academic grading** (zero code changes to existing nodes)
2. **Starts simple** (text-only PPTX, Phase 1)
3. **Iteratively adds capability** (RAG context, metadata, optional vision)
4. **Remains cost-effective** ($0.70/month for 100 submissions in Phases 1-2)
5. **Enables future scaling** (easy to add new business types, vision models)

**Total Implementation Time:** 7-8 weeks (Phases 1-7)
**MVP Ready:** Week 2 (Phase 1 completion)
**Demo Ready:** Week 3 (Phase 3 completion - can show supervisor)
**Production Ready:** Week 4 (Phases 1-4 completion)
**Cost:** $0.70-0.90/month (well under $5 budget)

The architecture's conditional routing ensures that adding business plan grading is **additive, not disruptive**—academic users see no changes, while business plan evaluation gets purpose-built logic and context.
