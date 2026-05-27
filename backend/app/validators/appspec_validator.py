"""
AppSpec Validator — Stage 3 (AppSpec) output validation.
Never throws. Returns structured ValidationReport.

Cross-layer checks:
- Every page → ≥1 API endpoint
- Every API endpoint has valid boundEntity from DataSchema
- Every auth role is defined in userRoles
- Every integrationHook references valid integration
- Every workflowStub references valid entities and integrations
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Set
from app.models.schemas import AppSpec, DataSchema, AppIntent, ValidationReport, ValidationError as VError
from app.integrations.registry import INTEGRATION_REGISTRY


def validate_appspec(spec: AppSpec, data_schema: DataSchema, intent: AppIntent) -> ValidationReport:
    """
    Validates Stage 3 AppSpec output with cross-layer checks.
    Returns ValidationReport — never raises.
    """
    errors: list[VError] = []
    warnings: list[VError] = []

    entity_names: Set[str] = {e.name for e in data_schema.entities}
    defined_routes: Set[str] = {p.route for p in spec.pages}
    api_paths: Set[str]      = {e.path for e in spec.apiEndpoints}
    valid_roles: Set[str]    = set(intent.userRoles) | {"admin", "user", "guest"}
    valid_integrations: Set[str] = set(INTEGRATION_REGISTRY.keys())

    # --- Pages ---
    if not spec.pages:
        errors.append(VError(code="SPEC_001", field="pages", message="AppSpec must contain at least one page"))

    for page in spec.pages:
        # Each page must reference ≥1 API endpoint
        page_api_refs = set(page.apiEndpoints)
        if not page_api_refs:
            warnings.append(VError(
                code="SPEC_002",
                field="pages",
                message=f"Page '{page.route}' has no API endpoint references",
                severity="warning",
                context={"page": page.route},
            ))

        # Bound entity must exist
        if page.boundEntity and page.boundEntity not in entity_names:
            errors.append(VError(
                code="SPEC_003",
                field="pages",
                message=f"Page '{page.route}' references non-existent entity '{page.boundEntity}'",
                context={"page": page.route, "entity": page.boundEntity},
            ))

        # allowedRoles must be valid
        for role in page.allowedRoles:
            if role not in valid_roles:
                warnings.append(VError(
                    code="SPEC_004",
                    field="pages",
                    message=f"Page '{page.route}' references unknown role '{role}'",
                    severity="warning",
                    context={"page": page.route, "role": role},
                ))

    # --- API Endpoints ---
    if not spec.apiEndpoints:
        errors.append(VError(code="SPEC_005", field="apiEndpoints", message="AppSpec must contain at least one API endpoint"))

    for endpoint in spec.apiEndpoints:
        # boundEntity must exist in DataSchema
        if endpoint.boundEntity and endpoint.boundEntity not in entity_names:
            errors.append(VError(
                code="SPEC_006",
                field="apiEndpoints",
                message=f"API endpoint '{endpoint.method} {endpoint.path}' references non-existent entity '{endpoint.boundEntity}'",
                context={"path": endpoint.path, "entity": endpoint.boundEntity},
            ))

        # allowedRoles must be valid
        for role in endpoint.allowedRoles:
            if role not in valid_roles:
                warnings.append(VError(
                    code="SPEC_007",
                    field="apiEndpoints",
                    message=f"Endpoint '{endpoint.path}' references unknown role '{role}'",
                    severity="warning",
                ))

    # --- Auth Rules ---
    for rule in spec.authRules:
        if rule.role not in valid_roles:
            warnings.append(VError(
                code="SPEC_008",
                field="authRules",
                message=f"Auth rule for unknown role '{rule.role}'",
                severity="warning",
            ))
        for route in rule.allowedRoutes:
            if route != "*" and route not in defined_routes:
                errors.append(VError(
                    code="SPEC_009",
                    field="authRules",
                    message=f"Auth rule for role '{rule.role}' references undefined route '{route}'",
                    context={"role": rule.role, "route": route},
                ))

    # --- Integration Hooks ---
    for hook in spec.integrationHooks:
        if hook.integrationId not in valid_integrations:
            errors.append(VError(
                code="SPEC_010",
                field="integrationHooks",
                message=f"IntegrationHook references unknown integration '{hook.integrationId}'",
                context={"integrationId": hook.integrationId},
            ))
        if hook.triggerEntity not in entity_names:
            errors.append(VError(
                code="SPEC_011",
                field="integrationHooks",
                message=f"IntegrationHook trigger entity '{hook.triggerEntity}' not in DataSchema",
                context={"triggerEntity": hook.triggerEntity},
            ))

    # --- Workflow Stubs ---
    for wf in spec.workflowStubs:
        if wf.integration not in valid_integrations:
            errors.append(VError(
                code="SPEC_012",
                field="workflowStubs",
                message=f"WorkflowStub '{wf.name}' references unknown integration '{wf.integration}'",
                context={"workflow": wf.name, "integration": wf.integration},
            ))
        if wf.triggerEntity not in entity_names:
            errors.append(VError(
                code="SPEC_013",
                field="workflowStubs",
                message=f"WorkflowStub '{wf.name}' trigger entity '{wf.triggerEntity}' not in DataSchema",
                context={"workflow": wf.name, "entity": wf.triggerEntity},
            ))

    return ValidationReport(
        stage="appspec_generation",
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        validatedAt=datetime.now(timezone.utc).isoformat(),
    )
