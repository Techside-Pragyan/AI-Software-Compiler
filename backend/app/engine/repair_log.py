"""
Repair Logger — tracks every repair attempt with full context.
"""
from __future__ import annotations
import time
from app.models.schemas import RepairAttempt, RepairLog, RepairStrategy, RepairOutcome


class RepairLogger:
    """
    Logs every repair attempt with strategy, error, outcome, latency.
    Attached to RepairEngine and exposed in pipeline result and SSE stream.
    """

    def __init__(self):
        self._log = RepairLog()

    def record(
        self,
        strategy: RepairStrategy,
        stage: str,
        error: str,
        outcome: RepairOutcome,
        retry_count: int,
        latency_ms: float,
        repaired_output: str | None = None,
        details: str | None = None,
    ) -> RepairAttempt:
        attempt = RepairAttempt(
            strategy=strategy,
            stage=stage,
            error=error[:500],  # Truncate long error messages
            outcome=outcome,
            retryCount=retry_count,
            latencyMs=latency_ms,
            repairedOutput=repaired_output[:1000] if repaired_output else None,
            details=details,
        )
        self._log.attempts.append(attempt)
        self._log.totalRetries += 1
        if outcome == RepairOutcome.repaired:
            self._log.totalRepaired += 1
        elif outcome == RepairOutcome.failed:
            self._log.totalFailed += 1
        return attempt

    def get_log(self) -> RepairLog:
        return self._log

    def to_dict(self) -> dict:
        return self._log.model_dump()
