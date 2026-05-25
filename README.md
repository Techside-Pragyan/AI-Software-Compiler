# AI Application Compiler System

## 1. Overview
This project is an AI Application Compiler System that translates natural language prompts directly into executable application configurations. It bridges the gap between raw idea generation and software infrastructure by outputting production-ready Database schemas, API routes, and UI components deterministically.

## 2. Architecture Diagram

```
User Prompt
   ↓
Intent Extraction
   ↓
System Design
   ↓
Schema Generation
   ↓
Validation Engine
   ↓
Repair Engine
   ↓
Runtime Preview
```

## 3. Features
- **Multi-stage pipeline**: Replaces monolithic generation with specific, constrained AI steps.
- **Validation engine**: Strictly checks for missing fields, hallucinated tables, and UI/API mismatch via heuristic cross-referencing.
- **Repair engine**: Isolates and repairs broken schemas recursively based on exact validation logs without rebuilding the entire system.
- **Runtime execution**: Next.js-powered mock engine that translates JSON UI schemas into dynamic components.
- **Deterministic generation**: Low-temperature structuring relying strictly on rigorous Pydantic typing.
- **Metrics dashboard**: Full transparency into generation latency, pipeline retries, and repair logs.

## 4. Tech Stack
- **Frontend**: Next.js (React), TypeScript, Tailwind CSS, Framer Motion
- **Backend**: FastAPI (Python), SQLAlchemy, Pydantic
- **AI Models**: Gemini API / OpenAI API
- **Database**: PostgreSQL (via psycopg2) / SQLite

## 5. Installation

To run locally, you need two terminal windows.

**Backend Setup:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
*(Ensure you have created a `.env` file with `GEMINI_API_KEY=...` in the backend folder)*

**Frontend Setup:**
```bash
cd frontend
npm install
npm run dev
```

## 6. Deployment Links
- **Frontend URL**: [To be added after Vercel deployment]
- **Backend URL**: [To be added after Render deployment]