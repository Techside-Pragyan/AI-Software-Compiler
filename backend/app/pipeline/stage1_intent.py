"""
Stage 1 — Intent Extraction Engine

Input:  str (raw natural language prompt)
Output: AppIntent (strictly typed, schema-safe)

Policy: If prompt is vague → proceed with documented assumptions.
Temperature: 0.1 (near-deterministic)
"""
from __future__ import annotations
import json
import logging
from typing import Optional

from app.pipeline.stage_base import PipelineStage
from app.models.schemas import AppIntent, AppType
from app.providers.gateway import get_gateway
from app.streaming.sse_manager import SSEManager

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert AI system architect operating as Stage 1 of an AI Compiler Pipeline.

Your ONLY job: extract structured intent from a natural language product requirement.

STRICT RULES:
- Respond with JSON ONLY — no markdown, no explanation, no extra keys
- appType must be one of: crm, ecommerce, saas, marketplace, internal_tool, lms, healthcare, fintech, social, analytics, other
- features: list of concrete feature strings (e.g. "authentication", "analytics", "real-time-notifications")
- entities: PascalCase entity names (e.g. "User", "Product", "Order") — minimum 2
- integrations_requested: lowercase integration IDs only (e.g. "whatsapp", "stripe", "slack") — empty list if none mentioned
- userRoles: user roles found in prompt (default to ["admin", "user"] if not mentioned)
- assumptions: document any assumptions made when the prompt was vague

VAGUE PROMPT POLICY:
- Never ask clarifying questions — always proceed
- Add assumptions[] to document what you assumed
- Use sensible defaults (authentication always assumed if user accounts implied)
"""


class IntentExtractionStage(PipelineStage[str, AppIntent]):
    """
    Stage 1: Extracts AppIntent from a raw natural language prompt.
    Uses the AI Gateway for provider-agnostic, config-driven model routing.
    """

    stage_name = "intent_extraction"

    def __init__(self, sse_manager: Optional[SSEManager] = None):
        super().__init__(sse_manager)
        self.gateway = get_gateway()

    def _run(self, prompt: str, job_id: str) -> AppIntent:
        logger.info(f"[Stage1] Extracting intent for job={job_id}")

        # Normalize empty/trivial prompts before sending
        normalized = prompt.strip()
        if len(normalized) < 10:
            normalized = f"{normalized}. Build a simple web application."
            logger.info(f"[Stage1] Short prompt detected, normalized: {normalized!r}")

        response = self.gateway.execute(
            stage="intentExtraction",
            prompt=normalized,
            system=SYSTEM_PROMPT,
            response_schema=AppIntent,
        )

        # Emit token/cost metrics via SSE
        self._emit("stage_metrics", job_id, {
            "stage": self.stage_name,
            "provider": response.provider,
            "model": response.model,
            "tokens_in": response.tokens_in,
            "tokens_out": response.tokens_out,
            "cost_usd": response.cost_usd,
            "latency_ms": response.latency_ms,
        })

        # Parse and validate
        try:
            data = json.loads(response.text)
            intent = AppIntent(**data)
            logger.info(f"[Stage1] Intent extracted: appName={intent.appName}, entities={intent.entities}")
            return intent
        except Exception as exc:
            logger.error(f"[Stage1] Parse failed: {exc}\nRaw: {response.text[:500]}")
            raise ValueError(f"IntentExtraction parse failure: {exc}") from exc
