"""
Intent Validator — Stage 1 output validation.
Never throws. Returns structured ValidationReport.
"""
from __future__ import annotations
from datetime import datetime, timezone
from app.models.schemas import AppIntent, AppType, ValidationReport, ValidationError as VError


KNOWN_INTEGRATIONS = {
    "slack", "whatsapp", "stripe", "gmail", "webhook", "twilio", "sendgrid",
    "hubspot", "salesforce", "jira", "github", "pagerduty", "zapier",
    "discord", "telegram", "shopify", "mailchimp", "zoom", "calendly",
}


def validate_intent(intent: AppIntent) -> ValidationReport:
    """
    Validates Stage 1 AppIntent output.
    Returns ValidationReport — never raises.
    """
    errors: list[VError] = []
    warnings: list[VError] = []

    # 1. appName must be non-empty
    if not intent.appName or not intent.appName.strip():
        errors.append(VError(
            code="INTENT_001",
            field="appName",
            message="appName must be a non-empty string",
        ))

    # 2. appType must be a valid enum value
    valid_types = {t.value for t in AppType}
    if intent.appType not in valid_types:
        errors.append(VError(
            code="INTENT_002",
            field="appType",
            message=f"appType '{intent.appType}' is invalid. Must be one of: {sorted(valid_types)}",
        ))

    # 3. features must be non-empty
    if not intent.features:
        errors.append(VError(
            code="INTENT_003",
            field="features",
            message="features list must not be empty",
        ))

    # 4. entities must have ≥2 entries
    if len(intent.entities) < 2:
        errors.append(VError(
            code="INTENT_004",
            field="entities",
            message=f"At least 2 entities required, got {len(intent.entities)}",
        ))

    # 5. Entity names should be PascalCase (warn, not error)
    for entity in intent.entities:
        if entity and not entity[0].isupper():
            warnings.append(VError(
                code="INTENT_005",
                field="entities",
                message=f"Entity '{entity}' should be PascalCase",
                severity="warning",
            ))

    # 6. Integration IDs should match known registry (warn unknown ones)
    for integ in intent.integrations_requested:
        if integ.lower() not in KNOWN_INTEGRATIONS:
            warnings.append(VError(
                code="INTENT_006",
                field="integrations_requested",
                message=f"Integration '{integ}' is not in the known registry — will be stubbed",
                severity="warning",
            ))

    # 7. userRoles must be non-empty
    if not intent.userRoles:
        warnings.append(VError(
            code="INTENT_007",
            field="userRoles",
            message="No userRoles defined — defaulting to ['admin', 'user']",
            severity="warning",
        ))

    return ValidationReport(
        stage="intent_extraction",
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        validatedAt=datetime.now(timezone.utc).isoformat(),
    )
