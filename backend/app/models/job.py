"""
Generation Job — in-memory job store with optional DB persistence.
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Any

from app.models.schemas import (
    AppIntent, DataSchema, AppSpec, ValidationReport,
    RepairLog, StageStatus, PipelineResult
)


@dataclass
class GenerationJob:
    """A single pipeline generation job."""
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    prompt: str = ""
    status: StageStatus = StageStatus.pending
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Stage outputs
    intent: Optional[AppIntent]           = None
    data_schema: Optional[DataSchema]     = None
    app_spec: Optional[AppSpec]           = None
    validation_report: Optional[ValidationReport] = None
    repair_log: RepairLog                 = field(default_factory=RepairLog)

    # Metrics
    cost_breakdown: Optional[dict]        = None
    total_cost_usd: float                 = 0.0
    total_latency_ms: float               = 0.0
    stages_completed: int                 = 0
    error: Optional[str]                  = None

    def update_status(self, status: StageStatus) -> None:
        self.status = status
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_summary(self) -> dict:
        """Lightweight summary for list endpoints."""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "prompt": self.prompt[:100] + ("..." if len(self.prompt) > 100 else ""),
            "created_at": self.created_at,
            "stages_completed": self.stages_completed,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_latency_ms": round(self.total_latency_ms, 2),
            "error": self.error,
        }

    def to_full_response(self) -> dict:
        """Full response including all pipeline outputs."""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "prompt": self.prompt,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "stages_completed": self.stages_completed,
            "intent":      self.intent.model_dump()      if self.intent      else None,
            "data_schema": self.data_schema.model_dump() if self.data_schema else None,
            "app_spec":    self.app_spec.model_dump()    if self.app_spec    else None,
            "validation_report": self.validation_report.model_dump() if self.validation_report else None,
            "repair_log":  self.repair_log.model_dump(),
            "cost_breakdown": self.cost_breakdown,
            "totals": {
                "cost_usd":   round(self.total_cost_usd,   6),
                "latency_ms": round(self.total_latency_ms, 2),
                "repair_count": self.repair_log.totalRetries,
            },
            "error": self.error,
        }


class JobStore:
    """In-memory job store. Production would use Redis or PostgreSQL."""

    def __init__(self):
        self._jobs: dict[str, GenerationJob] = {}

    def create(self, prompt: str) -> GenerationJob:
        job = GenerationJob(prompt=prompt)
        self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> Optional[GenerationJob]:
        return self._jobs.get(job_id)

    def list_all(self) -> list[GenerationJob]:
        return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)


_job_store: Optional[JobStore] = None

def get_job_store() -> JobStore:
    global _job_store
    if _job_store is None:
        _job_store = JobStore()
    return _job_store
