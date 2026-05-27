"""
Schema Validator — Stage 2 (DataSchema) output validation.
Never throws. Returns structured ValidationReport.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Set
from app.models.schemas import DataSchema, ValidationReport, ValidationError as VError


def validate_schema(schema: DataSchema) -> ValidationReport:
    """
    Validates Stage 2 DataSchema output.
    Returns ValidationReport — never raises.
    """
    errors: list[VError] = []
    warnings: list[VError] = []

    entity_names: Set[str] = {e.name for e in schema.entities}
    table_names: list[str] = []

    if not schema.entities:
        errors.append(VError(
            code="SCHEMA_001",
            field="entities",
            message="DataSchema must contain at least one entity",
        ))
        return ValidationReport(
            stage="schema_generation",
            passed=False,
            errors=errors,
            validatedAt=datetime.now(timezone.utc).isoformat(),
        )

    for entity in schema.entities:
        prefix = f"entity '{entity.name}'"

        # 1. No duplicate entity names
        # (tracked at the set level above, check table names for duplicates)
        if entity.tableName in table_names:
            errors.append(VError(
                code="SCHEMA_002",
                field="tableName",
                message=f"{prefix}: duplicate tableName '{entity.tableName}'",
                context={"entity": entity.name},
            ))
        else:
            table_names.append(entity.tableName)

        # 2. Table name must be snake_case
        if entity.tableName != entity.tableName.lower():
            errors.append(VError(
                code="SCHEMA_003",
                field="tableName",
                message=f"{prefix}: tableName '{entity.tableName}' must be snake_case (all lowercase)",
                context={"entity": entity.name},
            ))

        # 3. Fields must be non-empty
        if not entity.fields:
            errors.append(VError(
                code="SCHEMA_004",
                field="fields",
                message=f"{prefix}: must have at least one field",
                context={"entity": entity.name},
            ))

        # 4. tenantId must be present
        field_names = {f.name.lower() for f in entity.fields}
        if "tenantid" not in field_names:
            errors.append(VError(
                code="SCHEMA_005",
                field="fields",
                message=f"{prefix}: MISSING required 'tenantId' field for multi-tenancy",
                context={"entity": entity.name},
            ))

        # 5. id field must be present
        if "id" not in field_names:
            errors.append(VError(
                code="SCHEMA_006",
                field="fields",
                message=f"{prefix}: MISSING required 'id' primary key field",
                context={"entity": entity.name},
            ))

        # 6. Validate relation targets
        for rel in entity.relations:
            if rel.targetEntity not in entity_names:
                errors.append(VError(
                    code="SCHEMA_007",
                    field="relations",
                    message=f"{prefix}: relation targetEntity '{rel.targetEntity}' does not exist in schema",
                    context={"entity": entity.name, "targetEntity": rel.targetEntity},
                ))

        # 7. Warn if no indexes defined
        if not entity.indexes:
            warnings.append(VError(
                code="SCHEMA_008",
                field="indexes",
                message=f"{prefix}: no indexes defined — performance may be poor",
                severity="warning",
                context={"entity": entity.name},
            ))

    # 8. Check for bidirectional consistency
    relation_map: dict[str, Set[str]] = {}
    for entity in schema.entities:
        for rel in entity.relations:
            relation_map.setdefault(entity.name, set()).add(rel.targetEntity)

    for entity_name, targets in relation_map.items():
        for target in targets:
            if target in relation_map:
                if entity_name not in relation_map[target]:
                    warnings.append(VError(
                        code="SCHEMA_009",
                        field="relations",
                        message=f"Relation from '{entity_name}' → '{target}' has no reverse relation (may be intentional)",
                        severity="warning",
                    ))

    return ValidationReport(
        stage="schema_generation",
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        validatedAt=datetime.now(timezone.utc).isoformat(),
    )
