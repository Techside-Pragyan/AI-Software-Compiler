"""
Stage 2 — Schema Generation Engine

Input:  AppIntent
Output: DataSchema (EntitySchema[] with fields, relations, constraints)

Enforces:
- Every entity must have tenantId field
- snake_case table names
- Valid bidirectional relations
- No duplicate entity names
"""
from __future__ import annotations
import json
import logging
from typing import Optional

from app.pipeline.stage_base import PipelineStage
from app.models.schemas import AppIntent, DataSchema, EntitySchema, FieldDefinition, RelationDefinition, RelationType
from app.providers.gateway import get_gateway
from app.streaming.sse_manager import SSEManager

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert database architect operating as Stage 2 of an AI Compiler Pipeline.

Your job: Convert an AppIntent into a complete DataSchema with EntitySchema[] definitions.

STRICT RULES:
- Respond with JSON ONLY — no markdown, no explanation
- Every entity MUST include these base fields:
    1. id (uuid, required, unique, indexed)
    2. tenantId (uuid, required, indexed) — MANDATORY for multi-tenancy
    3. createdAt (timestamp, required)
    4. updatedAt (timestamp, required)
- tableName MUST be snake_case (e.g. "real_estate_leads", "deal_properties")
- Entity name must be PascalCase (e.g. "Lead", "Property", "Deal")
- Relations must be bidirectional — if Lead hasMany Properties, then Property belongsTo Lead
- Relation targetEntity MUST reference an entity name defined in this schema
- indexes: always index tenantId, foreign keys, and frequently-queried fields
- fieldType values: uuid, varchar, text, integer, decimal, boolean, timestamp, jsonb, enum

RELATION RULES:
- hasMany: the other entity holds a foreign key to this one
- belongsTo: this entity holds the foreign key
- hasOne: like hasMany but only one record

FIELD DESIGN:
- Add domain-specific fields that make sense for the app type
- Use decimal for monetary values, not float
- Add status fields as varchar with constraint notes
- Add description/notes as text (nullable)
"""


class SchemaGenerationStage(PipelineStage[AppIntent, DataSchema]):
    """
    Stage 2: Generates DataSchema from AppIntent.
    Enforces tenantId, snake_case, bidirectional relation consistency.
    """

    stage_name = "schema_generation"

    def __init__(self, sse_manager: Optional[SSEManager] = None):
        super().__init__(sse_manager)
        self.gateway = get_gateway()

    def _run(self, intent: AppIntent, job_id: str) -> DataSchema:
        logger.info(f"[Stage2] Generating schema for {len(intent.entities)} entities, job={job_id}")

        prompt = (
            f"Application Intent:\n{intent.model_dump_json(indent=2)}\n\n"
            f"Generate a complete DataSchema with EntitySchema for each entity: {intent.entities}.\n"
            f"Also create a User entity if not already in the list.\n"
            f"Ensure full bidirectional relation coverage between related entities."
        )

        response = self.gateway.execute(
            stage="schemaGeneration",
            prompt=prompt,
            system=SYSTEM_PROMPT,
            response_schema=DataSchema,
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
            data = json.loads(response.text)
            schema = DataSchema(**data)
            # Post-process: enforce tenantId and snake_case
            schema = self._enforce_schema_rules(schema, intent)
            logger.info(f"[Stage2] Schema generated: {len(schema.entities)} entities")
            return schema
        except Exception as exc:
            logger.error(f"[Stage2] Parse failed: {exc}\nRaw: {response.text[:500]}")
            raise ValueError(f"SchemaGeneration parse failure: {exc}") from exc

    def _enforce_schema_rules(self, schema: DataSchema, intent: AppIntent) -> DataSchema:
        """
        Programmatically enforce:
        1. Every entity has tenantId field
        2. snake_case table names
        3. id field exists
        """
        required_base_fields = {
            "id": FieldDefinition(name="id", fieldType="uuid", required=True, unique=True, indexed=True, defaultValue="gen_random_uuid()"),
            "tenantId": FieldDefinition(name="tenantId", fieldType="uuid", required=True, indexed=True),
            "createdAt": FieldDefinition(name="createdAt", fieldType="timestamp", required=True, defaultValue="now()"),
            "updatedAt": FieldDefinition(name="updatedAt", fieldType="timestamp", required=True, defaultValue="now()"),
        }

        fixed_entities = []
        for entity in schema.entities:
            existing_field_names = {f.name.lower() for f in entity.fields}

            # Add missing base fields at the front
            injected = []
            for field_name, field_def in required_base_fields.items():
                if field_name.lower() not in existing_field_names:
                    injected.append(field_def)
                    logger.info(f"[Stage2] Injected '{field_name}' into entity '{entity.name}'")

            # Fix snake_case table name
            table_name = entity.tableName
            if not table_name:
                table_name = _to_snake_case(entity.name) + "s"
            else:
                table_name = table_name.lower().replace(" ", "_").replace("-", "_")

            fixed_entities.append(entity.model_copy(update={
                "fields": injected + entity.fields,
                "tableName": table_name,
            }))

        return schema.model_copy(update={"entities": fixed_entities})


def _to_snake_case(name: str) -> str:
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
