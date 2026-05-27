"""
Cost Tracker — per-job cost aggregation across pipeline stages.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from app.config.cost_table import compute_cost


@dataclass
class StageCost:
    stage: str
    provider: str
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0


@dataclass
class JobCostBreakdown:
    job_id: str
    stages: list[StageCost] = field(default_factory=list)
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0

    def add_stage(self, stage: str, provider: str, model: str,
                  tokens_in: int, tokens_out: int, latency_ms: float) -> None:
        cost = compute_cost(provider, model, tokens_in, tokens_out)
        stage_cost = StageCost(
            stage=stage, provider=provider, model=model,
            tokens_in=tokens_in, tokens_out=tokens_out,
            cost_usd=cost, latency_ms=latency_ms,
        )
        self.stages.append(stage_cost)
        self.total_tokens_in  += tokens_in
        self.total_tokens_out += tokens_out
        self.total_cost_usd   += cost
        self.total_latency_ms += latency_ms

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "stages": [
                {
                    "stage": s.stage,
                    "provider": s.provider,
                    "model": s.model,
                    "tokens_in": s.tokens_in,
                    "tokens_out": s.tokens_out,
                    "cost_usd": s.cost_usd,
                    "latency_ms": round(s.latency_ms, 2),
                }
                for s in self.stages
            ],
            "totals": {
                "tokens_in": self.total_tokens_in,
                "tokens_out": self.total_tokens_out,
                "cost_usd": round(self.total_cost_usd, 6),
                "latency_ms": round(self.total_latency_ms, 2),
            },
        }


class CostTracker:
    """Singleton cost tracker for all active jobs."""

    def __init__(self):
        self._jobs: dict[str, JobCostBreakdown] = {}

    def get_or_create(self, job_id: str) -> JobCostBreakdown:
        if job_id not in self._jobs:
            self._jobs[job_id] = JobCostBreakdown(job_id=job_id)
        return self._jobs[job_id]

    def record(self, job_id: str, stage: str, provider: str, model: str,
               tokens_in: int, tokens_out: int, latency_ms: float) -> None:
        self.get_or_create(job_id).add_stage(stage, provider, model, tokens_in, tokens_out, latency_ms)

    def get_breakdown(self, job_id: str) -> Optional[dict]:
        breakdown = self._jobs.get(job_id)
        return breakdown.to_dict() if breakdown else None


_cost_tracker: Optional[CostTracker] = None

def get_cost_tracker() -> CostTracker:
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker
