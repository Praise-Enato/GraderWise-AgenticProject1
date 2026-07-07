# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

GradeWise is an AI-powered academic grading system. A **FastAPI + LangGraph** backend runs a self-correcting multi-agent grading workflow over an LLM + RAG; a **Next.js 16** frontend provides the educator/student dashboards. Deployed via Docker Compose behind an Nginx reverse proxy.

## Commands

All backend commands must run **from the repo root** — the app is imported as `backend.src.main:app` and RAG paths are resolved relative to the CWD (`./backend/data/...`).

```bash
make install          # install backend (uv venv + pip) AND frontend (npm)
make install-backend  # uv venv .venv, then pip install -r requirements.txt
make install-frontend # cd frontend && npm install

make run-backend      # uvicorn backend.src.main:app --reload --port 8000
make run-frontend     # cd frontend && npm run dev  (Turbopack, port 3000)
make dev              # run both concurrently (make -j 2)
make stop             # kill whatever is on ports 8000 and 3000

python backend/download_model.py   # pre-download the all-MiniLM-L6-v2 embedding model (needed once before RAG works)

cd frontend && npm run lint         # ESLint (flat config, eslint.config.mjs)
cd frontend && npm run build        # production build

python backend/test_langgraph.py    # smoke-test the LangGraph workflow with dummy data + mocked RAG (still hits the live LLM)
python backend/scripts/verify_imports.py   # confirm backend package imports resolve

docker-compose up --build           # full stack: nginx :80 -> frontend :3000 + backend :8000
```

There is no automated test suite (no pytest/jest). `test_langgraph.py` and the `backend/scripts/*` files are manual/benchmark harnesses that make real network calls.

## The grading agent (backend/src/agent.py)

This is the heart of the system — a LangGraph `StateGraph` with a self-correction loop. Read this file before touching any grading behavior.

```
retrieve (RAG) -> grade_submission (Grader) -> validate_grade (Judge) --valid--> generate_feedback (Mentor) -> END
                          ^                                            |
                          +------------- invalid, revision < 3 --------+
```

Non-obvious design decisions that span the file:

- **The LLM never computes the total score.** The Grader returns per-criteria JSON assessments (`awarded_points` each); Python sums them in `grade_submission`. Don't move summation into the prompt.
- **The Judge (`validate_grade`) is pure Python rule-checking, not an LLM.** It rejects internally-inconsistent grades (e.g. perfect score but critique lists errors, score exceeds max points) and loops back to the Grader with `grader_feedback`. `MAX_RETRIES = 3`, then it accepts best effort.
- **RAG queries with the rubric, not the submission** (`retrieve` node) — retrieving lecture notes by topic rather than by the student's (possibly wrong) answer. Query is truncated to 2000 chars.
- **The Mentor (`generate_feedback`) is Socratic by contract** — it is prompt-forbidden from stating the correct answer; it only gives hints. `confidence_score` is derived from the retry count, not the model.
- Agent actions are logged to `backend/logs/grading_debug.log` via `log_agent_action`.

## LLM & RAG configuration

- **LLM is DeepSeek-V3**, called through `langchain_openai.ChatOpenAI` pointed at `https://api.deepseek.com` (model `deepseek-chat`, `temperature=0`, JSON mode for structured nodes). Requires `DEEPSEEK_API_KEY` in a root `.env`.
- Configured independently in **two** places — `backend/src/agent.py` and `backend/src/rubric_parser.py`. Change both if you swap models.
- RAG: ChromaDB persisted at `./backend/data/chroma`, HuggingFace `all-MiniLM-L6-v2` embeddings (cached via `@lru_cache`), `RecursiveCharacterTextSplitter` (1000/200), top-k=10 retrieval. All in `backend/src/rag.py`.
- `requirements.txt` pins are load-bearing: `numpy==1.26.4` (avoids `np.float_` breakage), and pinned `chromadb==0.5.0` + OpenTelemetry versions to prevent telemetry crashes. Telemetry is also disabled via env vars at the top of `main.py`. Don't loosen these casually.

> **Docs drift:** `docs/specs/001_architecture.md` and `benchmark_testing.md` describe an earlier Groq/Llama-3 implementation and simpler Pydantic models. The live code uses DeepSeek-V3 and the richer models in `backend/src/models.py`. Trust the code, not those docs. Some scripts named in `benchmark_testing.md` (e.g. `prepare_asap.py`) no longer exist.

## Two API surfaces & the Nginx routing split

The frontend talks to **two different backends**, and Nginx routes by path prefix — this is the most error-prone part of the system.

- **`frontend/lib/api.ts`** (`GradeWiseAPI`, an axios client) calls the **Python backend directly** for grading/RAG (`/grade`, `/parse-rubric`, `/ingest`, `/extract-text`, `/extract-files-content`). Base URL is `NEXT_PUBLIC_API_URL` (baked at build time, defaults to `http://127.0.0.1:8000`).
- **Next.js route handlers** under `frontend/app/api/` handle submission records and batch grading:
  - `api/submissions` — CRUD over submission records
  - `api/educator/mass-grade` — batch-grades pending submissions by calling the Python backend server-side via `BACKEND_INTERNAL_URL` (`http://backend:8000` in Docker)
  - `api/grade` — saves a manual grade override

Nginx (`nginx/nginx.conf`) sends `/api/submissions` and `/api/educator` to the **frontend**, but strips the `/api` prefix and sends everything else under `/api/` to the **Python backend**. So `NEXT_PUBLIC_API_URL` is set to `http://<host>/api` in prod, while those two Next.js routes are deliberately excluded from the rewrite. When adding a Python endpoint or a Next.js route, update the Nginx location blocks accordingly.

## Data persistence

Submission records are stored in a **flat JSON file** at `frontend/data/submissions.json`, read/written directly by the Next.js route handlers with `fs`. **Prisma is installed** (`init_db.js`, `create_env.js`, `@prisma/client`) but is **not** the active persistence layer for submissions — don't assume a database. Both `submissions.json` and `.env` files are gitignored.

## Frontend layout

Next.js App Router (React 19, Tailwind v4, framer-motion, next-themes). Authenticated pages live under the `app/(dashboard)/` route group (dashboard, grading, mass-grading, submissions, students, history, analytics, settings, support); `app/page.tsx` is the marketing landing page. Route handlers under `app/api/` set `export const dynamic = 'force-dynamic'` because they touch the filesystem.
