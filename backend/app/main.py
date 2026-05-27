"""
AI Compiler Platform — FastAPI Application
Production-grade API layer for the AI pipeline.
"""
from __future__ import annotations
import json
import logging
from fastapi import FastAPI, HTTPException, Body, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import engine, get_db, Base
from app.models.db_models import Project
from app.models.job import get_job_store, GenerationJob
from app.models.schemas import StageStatus
from app.pipeline.orchestrator import run_pipeline_in_background
from app.streaming.sse_manager import get_sse_manager
from app.integrations.registry import list_integrations, get_implemented_integrations
from app.metrics.cost_tracker import get_cost_tracker

# Legacy pipeline (backward compat)
from app.compiler.pipeline import CompilerPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Software Compiler API",
    description="Production-grade AI-native application generation pipeline",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request/Response Models ──────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    prompt: str
    stream: bool = True  # Whether client will use SSE streaming

class RepairRequest(BaseModel):
    stage: str
    context: Optional[str] = None


# ─── NEW PIPELINE ENDPOINTS ───────────────────────────────────────────────────

@app.post("/api/generate")
async def start_generation(request: GenerateRequest):
    """
    Start a new pipeline generation job.
    Returns job_id immediately; pipeline runs async in background.
    Poll GET /api/generate/:jobId or stream GET /api/generate/:jobId/stream
    """
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt must be a non-empty string")

    job_store = get_job_store()
    job = job_store.create(prompt=request.prompt.strip())

    logger.info(f"[API] Created job {job.job_id} for prompt: {request.prompt[:80]}...")

    # Launch pipeline in background
    run_pipeline_in_background(job)

    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "message": "Pipeline started. Stream events at /api/generate/{job_id}/stream",
        "stream_url": f"/api/generate/{job.job_id}/stream",
        "poll_url":   f"/api/generate/{job.job_id}",
    }


@app.get("/api/generate/{job_id}")
async def get_generation_job(job_id: str):
    """
    Get full pipeline result for a job.
    Includes intent, data schema, app spec, validation report, repair log, cost breakdown.
    """
    job = get_job_store().get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return job.to_full_response()


@app.get("/api/generate/{job_id}/stream")
async def stream_generation(job_id: str):
    """
    SSE streaming endpoint for real-time pipeline progress.
    Emits: stage_start, stage_complete, stage_failed, repair_attempt, generation_complete
    Replays all past events on reconnect.
    """
    job = get_job_store().get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    sse_manager = get_sse_manager()

    async def event_generator():
        async for event_str in sse_manager.subscribe(job_id):
            yield event_str

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":       "no-cache",
            "X-Accel-Buffering":   "no",
            "Connection":          "keep-alive",
            "Access-Control-Allow-Origin": "*",
        },
    )


@app.post("/api/generate/{job_id}/repair")
async def trigger_repair(job_id: str, request: RepairRequest):
    """
    Manually trigger targeted repair on a failed stage.
    Useful for retrying a specific stage without restarting the full pipeline.
    """
    job = get_job_store().get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    if job.status != StageStatus.failed:
        raise HTTPException(status_code=400, detail="Job is not in failed state")

    # Re-run pipeline from the failed stage
    run_pipeline_in_background(job)
    return {"message": f"Repair triggered for job {job_id}", "job_id": job_id}


@app.get("/api/jobs")
async def list_jobs():
    """List all generation jobs with summary info."""
    jobs = get_job_store().list_all()
    return {"jobs": [j.to_summary() for j in jobs], "total": len(jobs)}


# ─── INTEGRATIONS ─────────────────────────────────────────────────────────────

@app.get("/api/integrations")
async def get_integrations(implemented_only: bool = False):
    """
    Return the full integration registry.
    Set ?implemented_only=true to return only fully implemented integrations.
    """
    integrations = get_implemented_integrations() if implemented_only else list_integrations()
    return {
        "integrations": [i.model_dump() for i in integrations],
        "total": len(integrations),
        "implemented": sum(1 for i in integrations if i.isFullyImplemented),
    }


@app.get("/api/integrations/{integration_id}")
async def get_integration(integration_id: str):
    """Get details for a specific integration."""
    from app.integrations.registry import get_integration as _get
    integration = _get(integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' not found")
    return integration.model_dump()


# ─── EVALUATION ───────────────────────────────────────────────────────────────

@app.post("/api/evaluate")
async def run_evaluation(background_tasks: BackgroundTasks, prompts: Optional[list[str]] = Body(None)):
    """
    Run the evaluation framework asynchronously.
    Results saved to evaluation-log.json
    """
    def _run_eval():
        from app.evaluation.framework import EvaluationFramework
        framework = EvaluationFramework()
        framework.run_evaluation(custom_prompts=prompts)

    background_tasks.add_task(_run_eval)
    return {"message": "Evaluation started in background. Results will be written to evaluation-log.json"}


@app.get("/api/evaluate/results")
async def get_evaluation_results():
    """Get the latest evaluation results."""
    import os
    result_path = "evaluation-log.json"
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="No evaluation results found. Run /api/evaluate first.")
    with open(result_path, "r") as f:
        return json.load(f)


# ─── LEGACY ENDPOINTS (backward compat) ───────────────────────────────────────

class CompileRequest(BaseModel):
    prompt: str

@app.post("/api/compile")
async def compile_application(request: CompileRequest):
    """
    Legacy compile endpoint. Use /api/generate for the new pipeline.
    Kept for backward compatibility.
    """
    try:
        pipeline = CompilerPipeline()
        config = pipeline.compile(request.prompt)
        return {
            "status": "success",
            "data": config.model_dump(),
            "metrics": pipeline.repair_engine.metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class SaveProjectRequest(BaseModel):
    name: str
    prompt: str
    intent_json: str = "{}"
    system_design_json: str = "{}"
    database_schema_json: str = "{}"
    api_schema_json: str = "{}"
    ui_schema_json: str = "{}"
    auth_rules_json: str = "{}"
    business_logic_json: str = "{}"
    metrics_json: str = "{}"

@app.post("/api/projects")
async def save_project(request: SaveProjectRequest, db: Session = Depends(get_db)):
    db_project = Project(
        name=request.name,
        prompt=request.prompt,
        intent_json=request.intent_json,
        system_design_json=request.system_design_json,
        database_schema_json=request.database_schema_json,
        api_schema_json=request.api_schema_json,
        ui_schema_json=request.ui_schema_json,
        auth_rules_json=request.auth_rules_json,
        business_logic_json=request.business_logic_json,
        metrics_json=request.metrics_json,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return {"status": "success", "id": db_project.id}

@app.get("/api/projects")
async def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return [{"id": p.id, "name": p.name, "created_at": p.created_at} for p in projects]


# ─── HEALTH ───────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "AI Software Compiler",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "generate":    "POST /api/generate",
            "stream":      "GET  /api/generate/:jobId/stream",
            "job_status":  "GET  /api/generate/:jobId",
            "repair":      "POST /api/generate/:jobId/repair",
            "integrations":"GET  /api/integrations",
            "evaluate":    "POST /api/evaluate",
        },
    }

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "2.0.0"}
