# AI Application Compiler System

A production-grade AI-powered Application Compiler that converts natural language prompts into fully structured, execution-ready applications using a deterministic, multi-stage AI orchestration pipeline.

## System Architecture

The system behaves like a software compiler, utilizing the following modular pipeline:
1. **Intent Extraction Layer**: Structures the user prompt into features, roles, and entities.
2. **System Design Layer**: Generates architectural flows and services.
3. **Schema Generation Layer**: Emits separate deterministic schemas for Database, API, UI, Auth, and Business Logic.
4. **Validation Engine**: Strictly enforces cross-layer consistency (e.g., UI references valid APIs, APIs reference valid DB tables).
5. **Selective Repair Engine**: Automatically isolates and repairs specific broken layers without regenerating the entire application.
6. **Execution Runtime**: Dynamically simulates the generated application schemas.

## Tech Stack

- **Backend**: FastAPI (Python), PostgreSQL / SQLite, SQLAlchemy, Pydantic, Gemini API.
- **Frontend**: Next.js (React), TypeScript, Tailwind CSS, Framer Motion, Lucide React.
- **Orchestration**: Multi-stage chained prompts with deterministic constraints.

## Local Setup

### 1. Backend Environment Setup
Create a `.env` file in the `/backend` directory:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=sqlite:///./app_studio.db # Or use postgresql://user:pass@localhost/db
```

### 2. Run the Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Run the Frontend
```bash
cd frontend
npm install
npm run dev
```

## Docker Deployment (Production)

To deploy the entire stack using Docker Compose:

```bash
# Build and run the containers
docker-compose up --build -d
```

This will spin up:
- The FastAPI Backend on port 8000
- The Next.js Frontend on port 3000
- A PostgreSQL Database instance

## Evaluation Framework

To run the bulk evaluation suite (testing 20 realistic and edge-case prompts against the validation and repair engines):
```bash
cd backend
python -m app.evaluation.framework
```

## Features Demonstrated
- Strong system thinking
- AI reliability engineering
- Validation architecture
- Repair orchestration
- Deterministic generation
- Execution-aware design