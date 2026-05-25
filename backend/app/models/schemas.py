from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

# ==========================================
# STAGE 1: INTENT EXTRACTION SCHEMAS
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
    app_type: str = Field(description="The type of application (e.g., SaaS, Marketplace, Internal Tool)")
    features: List[str] = Field(description="List of core features")
    roles: List[Role] = Field(description="User roles identified")
    entities: List[Entity] = Field(description="Core data entities identified from the prompt")

# ==========================================
# STAGE 2: SYSTEM DESIGN SCHEMAS
# ==========================================

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

# ==========================================
# STAGE 3: APPLICATION CONFIG SCHEMAS
# ==========================================

class FieldSchema(BaseModel):
    name: str
    type: str = Field(description="Database data type, e.g., varchar, integer, boolean, timestamp")
    required: bool
    constraints: Optional[str] = None

class TableSchema(BaseModel):
    name: str
    fields: List[FieldSchema]
    relationships: List[str] = Field(description="e.g., 'users.id -> posts.user_id'")
    indexes: List[str] = Field(default_factory=list)

class DatabaseSchema(BaseModel):
    tables: List[TableSchema]

class ApiEndpointSchema(BaseModel):
    method: str = Field(description="GET, POST, PUT, DELETE, PATCH")
    path: str
    description: str
    request_schema_ref: Optional[str] = Field(None, description="Description or ref of request payload")
    response_schema_ref: Optional[str] = Field(None, description="Description or ref of response payload")
    protected: bool = True
    allowed_roles: List[str] = Field(default_factory=list)

class ApiSchema(BaseModel):
    endpoints: List[ApiEndpointSchema]

class UiComponentSchema(BaseModel):
    name: str
    type: str = Field(description="e.g., form, list, dashboard, layout, table, card")
    props: Optional[Dict[str, Any]] = None
    children: Optional[List[str]] = Field(default_factory=list, description="Names of child components")

class UiPageSchema(BaseModel):
    route: str
    name: str
    layout: str
    components: List[UiComponentSchema]

class UiSchema(BaseModel):
    pages: List[UiPageSchema]
    navigation: List[str] = Field(description="List of routes accessible from primary navigation")

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
