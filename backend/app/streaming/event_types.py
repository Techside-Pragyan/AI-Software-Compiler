"""
SSE Event type definitions for the pipeline streaming system.
Each event has a stage, timestamp, latency, partial output, and repair logs.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Any, Literal
from datetime import datetime, timezone


class SSEEvent(BaseModel):
    """Base SSE event."""
    event_type: str
    stage: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    job_id: str = ""
    data: Optional[Any] = None

    def to_sse_string(self) -> str:
        """Format as SSE protocol string."""
        import json
        payload = self.model_dump()
        return f"event: {self.event_type}\ndata: {json.dumps(payload)}\n\n"


class StageStartEvent(SSEEvent):
    event_type: Literal["stage_start"] = "stage_start"
    stage: str


class StageCompleteEvent(SSEEvent):
    event_type: Literal["stage_complete"] = "stage_complete"
    stage: str
    latency_ms: float = 0.0
    partial_output: Optional[dict] = None


class StageFailedEvent(SSEEvent):
    event_type: Literal["stage_failed"] = "stage_failed"
    stage: str
    error: str
    latency_ms: float = 0.0


class StageMetricsEvent(SSEEvent):
    event_type: Literal["stage_metrics"] = "stage_metrics"
    stage: str
    provider: str = ""
    model: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0


class RepairAttemptEvent(SSEEvent):
    event_type: Literal["repair_attempt"] = "repair_attempt"
    strategy: str
    error: str
    outcome: str
    retry_count: int = 0
    latency_ms: float = 0.0


class GenerationCompleteEvent(SSEEvent):
    event_type: Literal["generation_complete"] = "generation_complete"
    total_latency_ms: float = 0.0
    total_cost_usd: float = 0.0
    stages_completed: int = 0
    repair_count: int = 0


class HeartbeatEvent(SSEEvent):
    event_type: Literal["heartbeat"] = "heartbeat"
