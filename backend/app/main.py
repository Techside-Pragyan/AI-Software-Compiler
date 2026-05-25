import json
from fastapi import FastAPI, HTTPException, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.compiler.pipeline import CompilerPipeline
from pydantic import BaseModel
from typing import List

from app.database import engine, get_db, Base
from app.models.db_models import Project

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="App Studio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CompileRequest(BaseModel):
    prompt: str

class SaveProjectRequest(BaseModel):
    name: str
    prompt: str
    intent_json: str
    system_design_json: str
    database_schema_json: str
    api_schema_json: str
    ui_schema_json: str
    auth_rules_json: str
    business_logic_json: str
    metrics_json: str

@app.get("/")
async def root():
    return {"message": "AI Software Compiler API is running. The frontend is deployed separately."}

@app.post("/api/compile")
async def compile_application(request: CompileRequest):
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
        metrics_json=request.metrics_json
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return {"status": "success", "id": db_project.id}

@app.get("/api/projects")
async def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return [{"id": p.id, "name": p.name, "created_at": p.created_at} for p in projects]

@app.get("/api/projects/{project_id}")
async def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "id": project.id,
        "name": project.name,
        "prompt": project.prompt,
        "intent": json.loads(project.intent_json) if project.intent_json else None,
        "system_design": json.loads(project.system_design_json) if project.system_design_json else None,
        "database_schema": json.loads(project.database_schema_json) if project.database_schema_json else None,
        "api_schema": json.loads(project.api_schema_json) if project.api_schema_json else None,
        "ui_schema": json.loads(project.ui_schema_json) if project.ui_schema_json else None,
        "auth_rules": json.loads(project.auth_rules_json) if project.auth_rules_json else None,
        "business_logic": json.loads(project.business_logic_json) if project.business_logic_json else None,
        "metrics": json.loads(project.metrics_json) if project.metrics_json else None,
    }

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
