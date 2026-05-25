from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from app.compiler.pipeline import CompilerPipeline
from pydantic import BaseModel

app = FastAPI(title="AI Application Compiler API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CompileRequest(BaseModel):
    prompt: str

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

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
