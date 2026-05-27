"""
SSE Manager — in-memory event store per job with replay support.

Features:
- Per-job event log (replay on reconnect)
- Thread-safe append
- Async queue for live streaming
- Heartbeat support
"""
from __future__ import annotations
import asyncio
import json
import logging
import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import AsyncIterator, Optional

logger = logging.getLogger(__name__)


class SSEManager:
    """
    Manages SSE event streams per job_id.
    Stores all events for replay on reconnect.
    """

    def __init__(self):
        # job_id → list of serialized event strings
        self._event_log: dict[str, list[str]] = defaultdict(list)
        # job_id → list of async queues (one per active subscriber)
        self._queues: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._lock = threading.Lock()

    def emit(self, job_id: str, event_type: str, data: dict) -> None:
        """
        Emit an SSE event for a job.
        Stores in event log and pushes to all active subscriber queues.
        """
        payload = {
            "event_type": event_type,
            "job_id": job_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data,
        }
        event_str = f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"

        with self._lock:
            self._event_log[job_id].append(event_str)
            queues = list(self._queues.get(job_id, []))

        # Push to all active subscriber queues (thread-safe via asyncio)
        for queue in queues:
            try:
                # Use call_soon_threadsafe if calling from a non-async context
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        queue.put(event_str), loop
                    )
                else:
                    queue.put_nowait(event_str)
            except Exception as exc:
                logger.debug(f"[SSE] Queue push failed (subscriber may have disconnected): {exc}")

    def get_event_log(self, job_id: str) -> list[str]:
        """Return all past events for a job (for reconnect replay)."""
        with self._lock:
            return list(self._event_log.get(job_id, []))

    def clear_job(self, job_id: str) -> None:
        """Clear event log for a completed job (optional cleanup)."""
        with self._lock:
            self._event_log.pop(job_id, None)

    async def subscribe(self, job_id: str) -> AsyncIterator[str]:
        """
        Async generator that yields SSE events for a job.
        Replays past events first, then streams new ones.
        Yields heartbeat every 15s to keep connection alive.
        """
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        # Register subscriber queue
        with self._lock:
            past_events = list(self._event_log.get(job_id, []))
            self._queues[job_id].append(queue)

        try:
            # Replay past events
            for event_str in past_events:
                yield event_str

            # Stream new events
            while True:
                try:
                    event_str = await asyncio.wait_for(queue.get(), timeout=15.0)
                    if event_str is None:  # Sentinel: stream closed
                        break
                    yield event_str
                except asyncio.TimeoutError:
                    # Heartbeat to keep connection alive
                    yield "event: heartbeat\ndata: {}\n\n"
        finally:
            with self._lock:
                queues = self._queues.get(job_id, [])
                if queue in queues:
                    queues.remove(queue)

    def close_job_stream(self, job_id: str) -> None:
        """Signal all subscribers that the stream for this job is done."""
        with self._lock:
            queues = list(self._queues.get(job_id, []))
        for queue in queues:
            try:
                queue.put_nowait(None)  # Sentinel
            except Exception:
                pass


# Singleton manager instance
_sse_manager: Optional[SSEManager] = None

def get_sse_manager() -> SSEManager:
    """Return singleton SSEManager instance."""
    global _sse_manager
    if _sse_manager is None:
        _sse_manager = SSEManager()
    return _sse_manager
