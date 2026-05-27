"""
Stage 3 — AppSpec Generation Engine

Input:  DataSchema + AppIntent
Output: AppSpec (pages, apiEndpoints, authRules, integrationHooks, workflowStubs)

Enforces:
- Every page maps to ≥1 API endpoint
- Every API endpoint has a bound entity from DataSchema
- Every workflow stub references valid entities and integrations
- Auth roles match userRoles from intent
"""
from __future__ import annotations
import json
import logging
from typing import Optional

from app.pipeline.stage_base import PipelineStage
from app.models.schemas import AppIntent, DataSchema, AppSpec
from app.providers.gateway import get_gateway
from app.integrations.registry import INTEGRATION_REGISTRY
from app.streaming.sse_manager import SSEManager

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert full-stack architect operating as Stage 3 of an AI Compiler Pipeline.

Your job: Convert a DataSchema + AppIntent into a complete AppSpec.

The AppSpec must contain:
1. pages[] — UI pages with routes, layouts, bound entities, components, and API references
2. apiEndpoints[] — REST endpoints with method, path, handler, bound entity, auth, rate limiting
3. authRules[] — per-role route access rules
4. permissionMatrix[] — CRUD permissions per role per entity
5. integrationHooks[] — events that trigger integration actions
6. workflowStubs[] — automation workflow stubs with payload schemas

STRICT RULES:
- JSON only — no markdown, no explanation
- Every page MUST list at least one apiEndpoints[] path it consumes
- Every API endpoint MUST have a boundEntity that exists in the DataSchema entities
- Every page route must be unique and start with "/"
- workflowStubs MUST reference integration IDs from this list: {integration_ids}
- workflowStubs MUST reference entity names that exist in the DataSchema
- authRules allowedRoutes must only contain routes defined in pages[]
- Roles must match the userRoles from the AppIntent

PAGE DESIGN:
- Always include: /dashboard, /login, /register
- Generate entity-specific pages: list view (/entity-name), detail view (/entity-name/:id), create/edit form
- Admin pages for admin role

API DESIGN:
- Standard CRUD: GET /api/entity, POST /api/entity, GET /api/entity/:id, PUT /api/entity/:id, DELETE /api/entity/:id
- Set rateLimitFlag=true for write operations and auth endpoints
- Set authRequired=true for all except /api/auth/login, /api/auth/register

INTEGRATION HOOKS:
- Generate hooks for each integration_requested
- Common triggers: created, updated, status_changed, deleted, payment_completed
"""


class AppSpecGenerationStage(PipelineStage[tuple, AppSpec]):
    """
    Stage 3: Generates complete AppSpec from DataSchema + AppIntent.
    """

    stage_name = "appspec_generation"

    def __init__(self, sse_manager: Optional[SSEManager] = None):
        super().__init__(sse_manager)
        self.gateway = get_gateway()

    def _run(self, inputs: tuple, job_id: str) -> AppSpec:
        data_schema, intent = inputs
        logger.info(f"[Stage3] Generating AppSpec, entities={len(data_schema.entities)}, job={job_id}")

        integration_ids = list(INTEGRATION_REGISTRY.keys())
        system = SYSTEM_PROMPT.replace("{integration_ids}", str(integration_ids))

        entity_names = [e.name for e in data_schema.entities]
        prompt = (
            f"AppIntent:\n{intent.model_dump_json(indent=2)}\n\n"
            f"DataSchema entities: {entity_names}\n"
            f"Full DataSchema:\n{data_schema.model_dump_json(indent=2)}\n\n"
            f"Requested integrations: {intent.integrations_requested}\n\n"
            f"Generate the complete AppSpec. Be comprehensive — include all CRUD pages, "
            f"all API endpoints, role-based auth rules, integration hooks for {intent.integrations_requested}, "
            f"and workflow stubs for each integration."
        )

        response = self.gateway.execute(
            stage="appSpecGeneration",
            prompt=prompt,
            system=system,
            response_schema=AppSpec,
        )

        self._emit("stage_metrics", job_id, {
            "stage": self.stage_name,
            "provider": response.provider,
            "model": response.model,
            "tokens_in": response.tokens_in,
            "tokens_out": response.tokens_out,
            "cost_usd": response.cost_usd,
            "latency_ms": response.latency_ms,
        })

        try:
            raw = json.loads(response.text)
            spec = AppSpec(**raw)
            logger.info(
                f"[Stage3] AppSpec: pages={len(spec.pages)}, endpoints={len(spec.apiEndpoints)}, "
                f"workflows={len(spec.workflowStubs)}, hooks={len(spec.integrationHooks)}"
            )
            return spec
        except Exception as exc:
            logger.error(f"[Stage3] Parse failed: {exc}\nRaw: {response.text[:500]}")
            raise ValueError(f"AppSpecGeneration parse failure: {exc}") from exc
