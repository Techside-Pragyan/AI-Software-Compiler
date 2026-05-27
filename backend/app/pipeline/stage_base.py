"""
Abstract base class for all pipeline stages.
Each stage has:
- Typed input/output
- Independent testability
- Validation hook
- SSE event emission
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, Callable, TYPE_CHECKING
import time

if TYPE_CHECKING:
    from app.streaming.sse_manager import SSEManager

InputT  = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class PipelineStage(ABC, Generic[InputT, OutputT]):
    """
    Abstract pipeline stage.
    Subclasses implement _run() and declare input_type / output_type.
    """

    stage_name: str = "unknown"

    def __init__(self, sse_manager: Optional["SSEManager"] = None):
        self.sse_manager = sse_manager

    def execute(self, input_data: InputT, job_id: str) -> OutputT:
        """
        Execute this stage. Emits SSE events and measures latency.
        Returns typed output or raises on unrecoverable failure.
        """
        start = time.time()
        self._emit("stage_start", job_id, {"stage": self.stage_name})

        try:
            result = self._run(input_data, job_id)
            latency_ms = (time.time() - start) * 1000
            self._emit("stage_complete", job_id, {
                "stage": self.stage_name,
                "latency_ms": latency_ms,
            })
            return result

        except Exception as exc:
            latency_ms = (time.time() - start) * 1000
            self._emit("stage_failed", job_id, {
                "stage": self.stage_name,
                "error": str(exc),
                "latency_ms": latency_ms,
            })
            raise

    @abstractmethod
    def _run(self, input_data: InputT, job_id: str) -> OutputT:
        """Core stage logic. Must be implemented by subclasses."""
        ...

    def _emit(self, event_type: str, job_id: str, data: dict) -> None:
        """Emit SSE event if manager is attached."""
        if self.sse_manager:
            self.sse_manager.emit(job_id, event_type, data)
