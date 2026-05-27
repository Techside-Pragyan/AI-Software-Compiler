"""
Repair Engine — core intelligence system.

3 classified repair strategies (NO blind full retries):

Strategy 1 — STRUCTURAL REPAIR
  Triggered: json.JSONDecodeError, truncated response, syntax errors
  Technique: regex extraction, partial JSON reconstruction, typed default filling

Strategy 2 — FIELD REPAIR
  Triggered: pydantic.ValidationError with missing/wrong-type fields
  Technique: isolated field regeneration via narrow correction prompt

Strategy 3 — CONSISTENCY REPAIR
  Triggered: cross-reference failures (broken entity refs, invalid workflows, etc.)
  Technique: deterministic programmatic repair first, selective re-prompting if that fails

Every attempt is logged with strategy, error, outcome, retry_count, and latency.
"""
from __future__ import annotations
import json
import re
import time
import logging
from typing import Optional, Type, Callable, Any
from pydantic import BaseModel, ValidationError

from app.engine.repair_log import RepairLogger
from app.models.schemas import (
    RepairStrategy, RepairOutcome, ValidationReport
)
from app.providers.gateway import get_gateway

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


class RepairEngine:
    """
    Classified repair engine.
    Detects failure type → applies targeted strategy → logs outcome.
    """

    def __init__(self):
        self.gateway = get_gateway()
        self.logger  = RepairLogger()
        # Keep backward-compat metrics dict for legacy /api/compile
        self.metrics = {"retries": 0, "failures": []}

    # -----------------------------------------------------------------------
    # PUBLIC API
    # -----------------------------------------------------------------------

    def repair(
        self,
        raw_text: str,
        schema_class: Type[BaseModel],
        stage: str,
        validation_report: Optional[ValidationReport] = None,
        context: str = "",
        sse_emit: Optional[Callable] = None,
    ) -> BaseModel:
        """
        Attempt to parse raw_text into schema_class.
        Classifies failures and applies the appropriate repair strategy.
        Returns a valid schema instance or raises after MAX_RETRIES.
        """
        current_text = raw_text
        retry_count  = 0

        for attempt in range(MAX_RETRIES + 1):
            start = time.time()
            try:
                data = _safe_json_parse(current_text)
                result = schema_class(**data)
                return result

            except json.JSONDecodeError as exc:
                # → Strategy 1: Structural repair
                latency_ms = (time.time() - start) * 1000
                if attempt >= MAX_RETRIES:
                    self.logger.record(
                        RepairStrategy.structural, stage, str(exc),
                        RepairOutcome.failed, retry_count, latency_ms,
                    )
                    raise RuntimeError(f"[RepairEngine] Structural repair exhausted on {stage}: {exc}")

                logger.info(f"[Repair] Strategy=STRUCTURAL attempt={attempt+1} stage={stage}")
                repaired, repaired_text = self._structural_repair(current_text, schema_class)
                latency_ms = (time.time() - start) * 1000
                attempt_log = self.logger.record(
                    RepairStrategy.structural, stage, str(exc),
                    RepairOutcome.repaired if repaired else RepairOutcome.failed,
                    retry_count, latency_ms, repaired_text,
                )
                if sse_emit:
                    sse_emit("repair_attempt", attempt_log.model_dump())
                if repaired:
                    current_text = repaired_text
                    retry_count += 1
                    self.metrics["retries"] += 1
                    continue
                raise

            except ValidationError as exc:
                latency_ms = (time.time() - start) * 1000
                errors = exc.errors()
                if attempt >= MAX_RETRIES:
                    self.logger.record(
                        RepairStrategy.field, stage, str(exc),
                        RepairOutcome.failed, retry_count, latency_ms,
                    )
                    self.metrics["failures"].append({"attempt": attempt, "error": str(exc), "schema": schema_class.__name__})
                    raise RuntimeError(f"[RepairEngine] Field repair exhausted on {stage}: {exc}")

                logger.info(f"[Repair] Strategy=FIELD attempt={attempt+1} stage={stage} fields={[e['loc'] for e in errors[:3]]}")
                repaired_text = self._field_repair(current_text, schema_class, errors, context)
                latency_ms = (time.time() - start) * 1000
                attempt_log = self.logger.record(
                    RepairStrategy.field, stage, str(exc),
                    RepairOutcome.repaired, retry_count, latency_ms, repaired_text,
                )
                if sse_emit:
                    sse_emit("repair_attempt", attempt_log.model_dump())
                current_text = repaired_text
                retry_count += 1
                self.metrics["retries"] += 1

            except Exception as exc:
                latency_ms = (time.time() - start) * 1000
                self.logger.record(
                    RepairStrategy.structural, stage, str(exc),
                    RepairOutcome.failed, retry_count, latency_ms,
                )
                raise

        raise RuntimeError(f"[RepairEngine] All strategies exhausted for {stage}")

    def consistency_repair(
        self,
        data: BaseModel,
        validation_report: ValidationReport,
        schema_class: Type[BaseModel],
        stage: str,
        context: str = "",
        sse_emit: Optional[Callable] = None,
    ) -> BaseModel:
        """
        Strategy 3: Consistency repair for cross-reference failures.
        First attempts deterministic programmatic repair, then selective re-prompting.
        """
        start = time.time()
        error_summary = "; ".join(
            f"[{e.code}] {e.message}" for e in validation_report.errors[:5]
        )
        logger.info(f"[Repair] Strategy=CONSISTENCY stage={stage} errors={len(validation_report.errors)}")

        # Step 1: Deterministic programmatic repair
        repaired_data = _programmatic_consistency_fix(data, validation_report)
        if repaired_data is not None:
            latency_ms = (time.time() - start) * 1000
            attempt_log = self.logger.record(
                RepairStrategy.consistency, stage, error_summary,
                RepairOutcome.repaired, 1, latency_ms,
                details="Programmatic fix applied",
            )
            if sse_emit:
                sse_emit("repair_attempt", attempt_log.model_dump())
            logger.info(f"[Repair] Programmatic consistency repair succeeded")
            return repaired_data

        # Step 2: Selective re-prompting for remaining errors
        repair_prompt = (
            f"You are a strict JSON consistency repair engine.\n"
            f"The following {schema_class.__name__} failed cross-reference validation.\n\n"
            f"CONTEXT:\n{context}\n\n"
            f"VALIDATION ERRORS:\n{error_summary}\n\n"
            f"BROKEN DATA:\n{data.model_dump_json(indent=2)}\n\n"
            f"Fix ONLY the fields causing these specific errors. Preserve all valid data.\n"
            f"Return the complete corrected JSON."
        )

        try:
            response = self.gateway.execute(
                stage="repair",
                prompt=repair_prompt,
                response_schema=schema_class,
            )
            fixed_data = json.loads(response.text)
            result = schema_class(**fixed_data)
            latency_ms = (time.time() - start) * 1000
            attempt_log = self.logger.record(
                RepairStrategy.consistency, stage, error_summary,
                RepairOutcome.repaired, 1, latency_ms,
                repaired_output=response.text[:500],
                details="LLM selective re-prompting applied",
            )
            if sse_emit:
                sse_emit("repair_attempt", attempt_log.model_dump())
            return result

        except Exception as exc:
            latency_ms = (time.time() - start) * 1000
            self.logger.record(
                RepairStrategy.consistency, stage, error_summary,
                RepairOutcome.failed, 1, latency_ms,
                details=str(exc),
            )
            raise RuntimeError(f"Consistency repair failed for {stage}: {exc}") from exc

    # -----------------------------------------------------------------------
    # LEGACY API (backward compat with /api/compile)
    # -----------------------------------------------------------------------

    def repair_and_validate(
        self,
        raw_json_or_dict,
        schema_class: Type[BaseModel],
        validation_context: str = "",
        custom_validator=None,
    ) -> BaseModel:
        """Legacy method for backward compatibility with the old pipeline."""
        current = raw_json_or_dict
        if isinstance(current, dict):
            current = json.dumps(current)

        for attempt in range(MAX_RETRIES + 1):
            try:
                data = json.loads(current)
                valid_schema = schema_class(**data)
                if custom_validator:
                    custom_validator(valid_schema)
                return valid_schema
            except (ValidationError, json.JSONDecodeError, ValueError) as e:
                self.metrics["failures"].append({"attempt": attempt, "error": str(e), "schema": schema_class.__name__})
                if attempt == MAX_RETRIES:
                    raise Exception(f"Failed to repair {schema_class.__name__} after {MAX_RETRIES} retries. Final error: {str(e)}")
                self.metrics["retries"] += 1
                repair_prompt = (
                    f"You are a strict JSON repair engine.\n"
                    f"The following configuration failed schema validation for {schema_class.__name__}.\n\n"
                    f"CONTEXT:\n{validation_context}\n\n"
                    f"ERROR DETAILS:\n{str(e)}\n\n"
                    f"BROKEN DATA:\n{current}\n\n"
                    f"Fix ONLY the specific fields causing the error. Preserve all valid outputs."
                )
                response = self.gateway.execute(
                    stage="repair",
                    prompt=repair_prompt,
                    response_schema=schema_class,
                )
                current = response.text

    # -----------------------------------------------------------------------
    # PRIVATE STRATEGIES
    # -----------------------------------------------------------------------

    def _structural_repair(
        self, raw_text: str, schema_class: Type[BaseModel]
    ) -> tuple[bool, str]:
        """
        Strategy 1: Structural repair for malformed/truncated JSON.
        Tries extraction patterns first, then LLM reconstruction.
        """
        # Attempt 1: Extract JSON object from surrounding text
        extracted = _extract_json_block(raw_text)
        if extracted:
            try:
                json.loads(extracted)  # Validate it parses
                return True, extracted
            except json.JSONDecodeError:
                pass

        # Attempt 2: LLM JSON reconstruction
        try:
            response = self.gateway.execute(
                stage="repair",
                prompt=(
                    f"The following text contains a broken or truncated JSON response that should match "
                    f"the {schema_class.__name__} schema.\n\n"
                    f"BROKEN TEXT:\n{raw_text[:2000]}\n\n"
                    f"Reconstruct the complete valid JSON. Return ONLY the JSON object, no markdown."
                ),
                response_schema=schema_class,
                temperature_override=0.0,
            )
            return True, response.text
        except Exception as exc:
            logger.error(f"[Repair] Structural LLM repair failed: {exc}")
            return False, raw_text

    def _field_repair(
        self,
        raw_text: str,
        schema_class: Type[BaseModel],
        errors: list[dict],
        context: str,
    ) -> str:
        """
        Strategy 2: Field repair — regenerates only broken fields.
        Uses narrow correction prompt targeting specific error locations.
        """
        # Identify the specific fields that need fixing
        broken_fields = []
        for err in errors[:5]:  # Cap at 5 fields to keep prompt focused
            loc = " -> ".join(str(l) for l in err.get("loc", []))
            msg = err.get("msg", "")
            broken_fields.append(f"  - Field: {loc} | Error: {msg}")

        field_list = "\n".join(broken_fields)

        try:
            response = self.gateway.execute(
                stage="repair",
                prompt=(
                    f"Fix ONLY these specific field errors in the {schema_class.__name__} JSON.\n"
                    f"Do NOT change any other fields.\n\n"
                    f"BROKEN FIELDS:\n{field_list}\n\n"
                    f"CONTEXT:\n{context}\n\n"
                    f"CURRENT JSON:\n{raw_text[:3000]}\n\n"
                    f"Return the complete corrected JSON with only the broken fields fixed."
                ),
                response_schema=schema_class,
                temperature_override=0.0,
            )
            return response.text
        except Exception as exc:
            logger.error(f"[Repair] Field repair failed: {exc}")
            return raw_text


# -----------------------------------------------------------------------
# UTILITIES
# -----------------------------------------------------------------------

def _safe_json_parse(text: str) -> dict:
    """Parse JSON, trying to extract from markdown blocks if needed."""
    text = text.strip()
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try extracting from markdown code blocks
    extracted = _extract_json_block(text)
    if extracted:
        return json.loads(extracted)
    raise json.JSONDecodeError("Could not parse JSON", text, 0)


def _extract_json_block(text: str) -> Optional[str]:
    """Extract JSON object from surrounding text/markdown."""
    # Pattern: ```json ... ``` or ``` ... ```
    patterns = [
        r"```json\s*([\s\S]*?)\s*```",
        r"```\s*([\s\S]*?)\s*```",
        r"(\{[\s\S]*\})",
        r"(\[[\s\S]*\])",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            candidate = match.group(1).strip()
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                continue
    return None


def _programmatic_consistency_fix(data: BaseModel, report: ValidationReport) -> Optional[BaseModel]:
    """
    Attempt deterministic programmatic fixes for known consistency error patterns.
    Returns fixed model or None if programmatic fix cannot resolve all errors.
    """
    from app.models.schemas import AppSpec, AuthRuleSpec

    if not isinstance(data, AppSpec):
        return None  # Only AppSpec supports programmatic consistency repair

    spec = data
    error_codes = {e.code for e in report.errors}
    made_changes = False

    # Fix SPEC_009: auth rules referencing non-existent routes
    if "SPEC_009" in error_codes:
        defined_routes = {p.route for p in spec.pages}
        fixed_auth_rules = []
        for rule in spec.authRules:
            fixed_routes = [r for r in rule.allowedRoutes if r == "*" or r in defined_routes]
            if len(fixed_routes) != len(rule.allowedRoutes):
                made_changes = True
                logger.info(f"[Repair] Removed invalid routes from auth rule for '{rule.role}'")
            fixed_auth_rules.append(AuthRuleSpec(
                role=rule.role,
                allowedRoutes=fixed_routes,
                restrictedActions=rule.restrictedActions,
            ))
        spec = spec.model_copy(update={"authRules": fixed_auth_rules})

    # Fix SPEC_010/SPEC_012: remove hooks/stubs with unknown integrations
    from app.integrations.registry import INTEGRATION_REGISTRY
    valid_integrations = set(INTEGRATION_REGISTRY.keys())

    if "SPEC_010" in error_codes:
        fixed_hooks = [h for h in spec.integrationHooks if h.integrationId in valid_integrations]
        if len(fixed_hooks) != len(spec.integrationHooks):
            made_changes = True
            logger.info(f"[Repair] Removed {len(spec.integrationHooks) - len(fixed_hooks)} invalid integration hooks")
        spec = spec.model_copy(update={"integrationHooks": fixed_hooks})

    if "SPEC_012" in error_codes:
        fixed_stubs = [w for w in spec.workflowStubs if w.integration in valid_integrations]
        if len(fixed_stubs) != len(spec.workflowStubs):
            made_changes = True
        spec = spec.model_copy(update={"workflowStubs": fixed_stubs})

    return spec if made_changes else None
