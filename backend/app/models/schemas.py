"""
Core type definitions for the AI Compiler Pipeline.
All pipeline stages use these typed interfaces for input/output contracts.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Literal
from enum import Enum


# ==========================================
# ENUMS
# ==========================================

class AppType(str, Enum):
    crm = "crm"
    ecommerce = "ecommerce"
    saas = "saas"
    marketplace = "marketplace"
    internal_tool = "internal_tool"
    lms = "lms"
    healthcare = "healthcare"
    fintech = "fintech"
    social = "social"
    analytics = "analytics"
    other = "other"

class RelationType(str, Enum):
    has_many = "hasMany"
    belongs_to = "belongsTo"
    has_one = "hasOne"

class AuthType(str, Enum):
    oauth2 = "oauth2"
    api_key = "api_key"
    webhook = "webhook"
    basic = "basic"
    none = "none"

class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"

class RepairStrategy(str, Enum):
    structural = "structural_repair"
    field = "field_repair"
    consistency = "consistency_repair"

class RepairOutcome(str, Enum):
    repaired = "repaired"
    failed = "failed"
    skipped = "skipped"

class StageStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    repaired = "repaired"


# ==========================================
# STAGE 1 — APP INTENT (Intent Extraction)
# ==========================================

class AppIntent(BaseModel):
    """Strict typed output of Stage 1: Intent Extraction Engine."""
    appName: str = Field(description="Human-readable name of the application")
    appType: AppType = Field(description="Application category type")
    features: List[str] = Field(description="Core features list (e.g. authentication, analytics)")
    entities: List[str] = Field(description="Core data entities (e.g. User, Product, Order)")
    integrations_requested: List[str] = Field(
        default_factory=list,
        description="External integrations mentioned (e.g. whatsapp, stripe)"
    )
    userRoles: List[str] = Field(
        default_factory=lambda: ["admin", "user"],
        description="User roles in the application"
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="Assumptions made when prompt was vague"
    )


# ==========================================
# STAGE 2 — DATA SCHEMA (Schema Generation)
# ==========================================

class FieldDefinition(BaseModel):
    """Typed field in an entity schema."""
    name: str
    fieldType: str = Field(description="e.g. varchar, integer, boolean, timestamp, uuid, text, decimal")
    required: bool = True
    unique: bool = False
    indexed: bool = False
    defaultValue: Optional[str] = None
    constraints: Optional[str] = None

class RelationDefinition(BaseModel):
    """Typed relation between two entities."""
    relationType: RelationType
    targetEntity: str = Field(description="Name of the related entity")
    foreignKey: Optional[str] = None
    throughTable: Optional[str] = None

class EntitySchema(BaseModel):
    """Schema definition for a single data entity."""
    name: str = Field(description="PascalCase entity name (e.g. Lead, Property)")
    tableName: str = Field(description="snake_case database table name")
    fields: List[FieldDefinition] = Field(description="All fields including tenantId, id, timestamps")
    relations: List[RelationDefinition] = Field(default_factory=list)
    indexes: List[str] = Field(default_factory=list, description="List of indexed field names")
    primaryKey: str = Field(default="id")

class DataSchema(BaseModel):
    """Stage 2 output: full database schema with entities and relations."""
    entities: List[EntitySchema]


# ==========================================
# STAGE 3 — APP SPEC (AppSpec Generation)
# ==========================================

class UiComponent(BaseModel):
    name: str
    componentType: str = Field(description="e.g. DataTable, Form, Chart, KanbanBoard, Card")
    props: Optional[Dict[str, Any]] = None

class PageSpec(BaseModel):
    """A UI page specification."""
    name: str
    route: str
    layout: str = Field(description="e.g. DashboardLayout, AuthLayout, FullWidthLayout")
    boundEntity: Optional[str] = Field(None, description="Primary entity this page manages")
    components: List[UiComponent] = Field(default_factory=list)
    apiEndpoints: List[str] = Field(default_factory=list, description="API paths this page consumes")
    requiresAuth: bool = True
    allowedRoles: List[str] = Field(default_factory=list)

class ApiEndpointSpec(BaseModel):
    """A single REST API endpoint specification."""
    path: str
    method: HttpMethod
    handlerDescription: str
    boundEntity: Optional[str] = None
    authRequired: bool = True
    rateLimitFlag: bool = False
    allowedRoles: List[str] = Field(default_factory=list)
    requestSchema: Optional[Dict[str, Any]] = None
    responseSchema: Optional[Dict[str, Any]] = None

class PermissionMatrix(BaseModel):
    """CRUD permission matrix per role per entity."""
    role: str
    entity: str
    canCreate: bool = False
    canRead: bool = True
    canUpdate: bool = False
    canDelete: bool = False

class IntegrationHook(BaseModel):
    """A hook connecting an event to an integration action."""
    integrationId: str
    triggerEntity: str
    triggerEvent: str = Field(description="e.g. created, updated, status_changed, deleted")
    action: str = Field(description="Integration action name e.g. send_template_message")
    payloadMapping: Dict[str, str] = Field(default_factory=dict)

class WorkflowStub(BaseModel):
    """An automation workflow stub."""
    name: str
    triggerEntity: str
    triggerEvent: str
    integration: str
    action: str
    payloadSchema: Dict[str, Any] = Field(default_factory=dict)
    fieldMappings: Dict[str, str] = Field(default_factory=dict)
    actionMetadata: Optional[Dict[str, Any]] = None

class AuthRuleSpec(BaseModel):
    """Auth rule per role."""
    role: str
    allowedRoutes: List[str] = Field(default_factory=list)
    restrictedActions: List[str] = Field(default_factory=list)

class AppSpec(BaseModel):
    """Stage 3 output: complete application specification."""
    pages: List[PageSpec]
    apiEndpoints: List[ApiEndpointSpec]
    authRules: List[AuthRuleSpec]
    permissionMatrix: List[PermissionMatrix] = Field(default_factory=list)
    integrationHooks: List[IntegrationHook] = Field(default_factory=list)
    workflowStubs: List[WorkflowStub] = Field(default_factory=list)


# ==========================================
# VALIDATION ENGINE OUTPUTS
# ==========================================

class ValidationError(BaseModel):
    """A single structured validation error."""
    code: str
    field: Optional[str] = None
    message: str
    severity: Literal["error", "warning", "info"] = "error"
    context: Optional[Dict[str, Any]] = None

class ValidationReport(BaseModel):
    """Structured validation report returned by every validator — never throws."""
    stage: str
    passed: bool
    errors: List[ValidationError] = Field(default_factory=list)
    warnings: List[ValidationError] = Field(default_factory=list)
    validatedAt: str = ""


# ==========================================
# REPAIR ENGINE OUTPUTS
# ==========================================

class RepairAttempt(BaseModel):
    """A single repair attempt log entry."""
    strategy: RepairStrategy
    stage: str
    error: str
    outcome: RepairOutcome
    retryCount: int
    latencyMs: float
    repairedOutput: Optional[str] = None
    details: Optional[str] = None

class RepairLog(BaseModel):
    """Full repair log for a pipeline run."""
    attempts: List[RepairAttempt] = Field(default_factory=list)
    totalRetries: int = 0
    totalRepaired: int = 0
    totalFailed: int = 0


# ==========================================
# STAGE METRICS
# ==========================================

class StageMetrics(BaseModel):
    """Per-stage execution metrics."""
    stage: str
    status: StageStatus
    latencyMs: float
    provider: str
    model: str
    tokensIn: int = 0
    tokensOut: int = 0
    costUsd: float = 0.0
    repairAttempts: int = 0
    validationPassed: bool = True


# ==========================================
# PIPELINE OUTPUT (Full Result)
# ==========================================

class PipelineResult(BaseModel):
    """Complete pipeline execution result."""
    jobId: str
    prompt: str
    intent: Optional[AppIntent] = None
    dataSchema: Optional[DataSchema] = None
    appSpec: Optional[AppSpec] = None
    validationReport: Optional[ValidationReport] = None
    repairLog: RepairLog = Field(default_factory=RepairLog)
    stageMetrics: List[StageMetrics] = Field(default_factory=list)
    totalCostUsd: float = 0.0
    totalLatencyMs: float = 0.0
    status: StageStatus = StageStatus.pending


# ==========================================
# LEGACY SCHEMAS (backward compatibility with /api/compile)
# ==========================================

class Entity(BaseModel):
    name: str
    description: str
    attributes: List[str]

class Role(BaseModel):
    name: str
    description: str
    permissions: List[str]

class IntentSchema(BaseModel):
    app_type: str = Field(description="The type of application")
    features: List[str]
    roles: List[Role]
    entities: List[Entity]

class ServiceSchema(BaseModel):
    name: str
    description: str
    dependencies: List[str] = Field(default_factory=list)

class FlowSchema(BaseModel):
    name: str
    steps: List[str]

class SystemDesignSchema(BaseModel):
    services: List[ServiceSchema]
    flows: List[FlowSchema]
    architecture_modules: List[str]

class FieldSchema(BaseModel):
    name: str
    type: str
    required: bool
    constraints: Optional[str] = None

class TableSchema(BaseModel):
    name: str
    fields: List[FieldSchema]
    relationships: List[str]
    indexes: List[str] = Field(default_factory=list)

class DatabaseSchema(BaseModel):
    tables: List[TableSchema]

class ApiEndpointSchema(BaseModel):
    method: str
    path: str
    description: str
    request_schema_ref: Optional[str] = None
    response_schema_ref: Optional[str] = None
    protected: bool = True
    allowed_roles: List[str] = Field(default_factory=list)

class ApiSchema(BaseModel):
    endpoints: List[ApiEndpointSchema]

class UiComponentSchema(BaseModel):
    name: str
    type: str
    props: Optional[Dict[str, Any]] = None
    children: Optional[List[str]] = Field(default_factory=list)

class UiPageSchema(BaseModel):
    route: str
    name: str
    layout: str
    components: List[UiComponentSchema]

class UiSchema(BaseModel):
    pages: List[UiPageSchema]
    navigation: List[str]

class AuthRuleSchema(BaseModel):
    role: str
    allowed_routes: List[str]
    restricted_actions: List[str]

class AuthRulesSchema(BaseModel):
    rules: List[AuthRuleSchema]

class BusinessLogicRuleSchema(BaseModel):
    name: str
    condition: str
    action: str
    requires_subscription: bool = False

class BusinessLogicSchema(BaseModel):
    rules: List[BusinessLogicRuleSchema]

class ApplicationConfigSchema(BaseModel):
    intent: IntentSchema
    system_design: SystemDesignSchema
    database_schema: DatabaseSchema
    api_schema: ApiSchema
    ui_schema: UiSchema
    auth_rules: AuthRulesSchema
    business_logic: BusinessLogicSchema
