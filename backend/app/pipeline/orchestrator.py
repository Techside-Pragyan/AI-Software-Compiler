"""
Pipeline Orchestrator — coordinates all 3 stages with:
- Per-stage validation
- Repair on failure
- SSE event emission
- Cost tracking
- Repair logging
"""
from __future__ import annotations
import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from app.models.schemas import StageStatus, ValidationReport
from app.models.job import GenerationJob, get_job_store
from app.pipeline.stage1_intent import IntentExtractionStage
from app.pipeline.stage2_schema import SchemaGenerationStage
from app.pipeline.stage3_appspec import AppSpecGenerationStage
from app.validators.intent_validator import validate_intent
from app.validators.schema_validator import validate_schema
from app.validators.appspec_validator import validate_appspec
from app.engine.repair import RepairEngine
from app.streaming.sse_manager import SSEManager, get_sse_manager
from app.metrics.cost_tracker import get_cost_tracker
from app.workflow.stub_generator import generate_workflow_stubs

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4)


class PipelineOrchestrator:
    """
    Orchestrates the 3-stage AI compiler pipeline.
    Validates after each stage, repairs on failure, streams SSE events.
    """

    def __init__(self, job: GenerationJob, sse_manager: Optional[SSEManager] = None):
        self.job         = job
        self.sse         = sse_manager or get_sse_manager()
        self.repair      = RepairEngine()
        self.cost        = get_cost_tracker()
        self.job_store   = get_job_store()

        # Wire SSE into stages
        self.stage1 = IntentExtractionStage(sse_manager=self.sse)
        self.stage2 = SchemaGenerationStage(sse_manager=self.sse)
        self.stage3 = AppSpecGenerationStage(sse_manager=self.sse)

    def _emit(self, event_type: str, data: dict) -> None:
        self.sse.emit(self.job.job_id, event_type, data)

    def run(self) -> GenerationJob:
        """
        Execute the full pipeline synchronously.
        Called from a background thread.
        """
        start_time = time.time()
        job = self.job
        job.update_status(StageStatus.running)

        try:
            # ─── STAGE 1: Intent Extraction ────────────────────────────────
            logger.info(f"[Orchestrator] Starting Stage 1 for job={job.job_id}")
            intent = self.stage1.execute(job.prompt, job.job_id)
            job.intent = intent
            job.stages_completed = 1

            # Validate Stage 1 output
            intent_report = validate_intent(intent)
            if not intent_report.passed:
                logger.warning(f"[Orchestrator] Stage 1 validation warnings: {[e.code for e in intent_report.errors]}")
                # Non-fatal: log and continue (intent extraction is robust)
                self._emit("validation_warning", {
                    "stage": "intent_extraction",
                    "errors": [e.model_dump() for e in intent_report.errors],
                })

            # ─── STAGE 2: Schema Generation ────────────────────────────────
            logger.info(f"[Orchestrator] Starting Stage 2 for job={job.job_id}")
            data_schema = self.stage2.execute(intent, job.job_id)

            # Validate Stage 2 output
            schema_report = validate_schema(data_schema)
            if not schema_report.passed:
                logger.warning(f"[Orchestrator] Stage 2 validation failed: {[e.code for e in schema_report.errors]}")
                self._emit("repair_triggered", {"stage": "schema_generation", "reason": "validation_failed"})
                # Field/consistency repair attempt
                data_schema = self._repair_schema(data_schema, schema_report)

            job.data_schema = data_schema
            job.stages_completed = 2

            # ─── STAGE 3: AppSpec Generation ───────────────────────────────
            logger.info(f"[Orchestrator] Starting Stage 3 for job={job.job_id}")
            app_spec = self.stage3.execute((data_schema, intent), job.job_id)

            # Augment with workflow stubs from generator (deterministic)
            generated_stubs = generate_workflow_stubs(intent, data_schema)
            if generated_stubs:
                # Merge generated stubs (avoid duplicates by name)
                existing_names = {s.name for s in app_spec.workflowStubs}
                new_stubs = [s for s in generated_stubs if s.name not in existing_names]
                app_spec = app_spec.model_copy(update={
                    "workflowStubs": app_spec.workflowStubs + new_stubs
                })
                logger.info(f"[Orchestrator] Added {len(new_stubs)} workflow stubs from generator")

            # Validate Stage 3 output
            spec_report = validate_appspec(app_spec, data_schema, intent)
            if not spec_report.passed:
                logger.warning(f"[Orchestrator] Stage 3 validation failed: {[e.code for e in spec_report.errors]}")
                self._emit("repair_triggered", {"stage": "appspec_generation", "reason": "validation_failed"})
                app_spec = self._repair_appspec(app_spec, spec_report, data_schema, intent)
                # Re-validate after repair
                spec_report = validate_appspec(app_spec, data_schema, intent)

            job.app_spec         = app_spec
            job.validation_report = spec_report
            job.stages_completed = 3

            # ─── Finalize ─────────────────────────────────────────────────
            job.repair_log        = self.repair.logger.get_log()
            job.cost_breakdown    = self.cost.get_breakdown(job.job_id)
            job.total_latency_ms  = (time.time() - start_time) * 1000
            job.total_cost_usd    = job.cost_breakdown["totals"]["cost_usd"] if job.cost_breakdown else 0.0
            job.update_status(StageStatus.completed)

            self._emit("generation_complete", {
                "total_latency_ms": job.total_latency_ms,
                "total_cost_usd": job.total_cost_usd,
                "stages_completed": job.stages_completed,
                "repair_count": job.repair_log.totalRetries,
            })
            self.sse.close_job_stream(job.job_id)
            logger.info(f"[Orchestrator] Job {job.job_id} completed in {job.total_latency_ms:.0f}ms, cost=${job.total_cost_usd:.4f}")

        except Exception as exc:
            logger.error(f"[Orchestrator] Job {job.job_id} failed: {exc}", exc_info=True)
            job.error = str(exc)
            job.repair_log = self.repair.logger.get_log()
            job.update_status(StageStatus.failed)
            self._emit("stage_failed", {
                "stage": f"stage_{job.stages_completed + 1}",
                "error": str(exc),
                "latency_ms": (time.time() - start_time) * 1000,
            })
            self.sse.close_job_stream(job.job_id)

        return job

    def _repair_schema(self, data_schema, report: ValidationReport):
        """Apply consistency repair to DataSchema."""
        from app.models.schemas import DataSchema
        try:
            return self.repair.consistency_repair(
                data=data_schema,
                validation_report=report,
                schema_class=DataSchema,
                stage="schema_generation",
                sse_emit=lambda evt, d: self._emit(evt, d),
            )
        except Exception as exc:
            logger.error(f"[Orchestrator] Schema repair failed: {exc}")
            return data_schema  # Return as-is, don't block pipeline

    def _repair_appspec(self, app_spec, report: ValidationReport, data_schema, intent):
        """Apply consistency repair to AppSpec."""
        from app.models.schemas import AppSpec
        try:
            return self.repair.consistency_repair(
                data=app_spec,
                validation_report=report,
                schema_class=AppSpec,
                stage="appspec_generation",
                context=f"DataSchema entities: {[e.name for e in data_schema.entities]}\nUserRoles: {intent.userRoles}",
                sse_emit=lambda evt, d: self._emit(evt, d),
            )
        except Exception as exc:
            logger.error(f"[Orchestrator] AppSpec repair failed: {exc}")
            return app_spec  # Return as-is


def run_pipeline_in_background(job: GenerationJob) -> None:
    """
    Launch the pipeline in a background thread.
    Called from the FastAPI endpoint.
    """
    def _run():
        orchestrator = PipelineOrchestrator(job)
        orchestrator.run()

    _executor.submit(_run)
