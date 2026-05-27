"""
Integration data models for the Integration Registry.
"""
from __future__ import annotations
from pydantic import BaseModel
from typing import List, Optional
from app.models.schemas import AuthType


class IntegrationTrigger(BaseModel):
    id: str
    name: str
    description: str
    entityEvent: Optional[str] = None  # e.g. "status_changed"


class IntegrationAction(BaseModel):
    id: str
    name: str
    description: str
    requiredParams: List[str] = []
    optionalParams: List[str] = []


class Integration(BaseModel):
    """Full integration definition."""
    id: str
    displayName: str
    description: str
    authType: AuthType
    category: str  # messaging, payments, email, crm, devops, generic
    logoColor: str = "#6366f1"  # Brand color for UI
    isFullyImplemented: bool = True
    triggers: List[IntegrationTrigger] = []
    actions: List[IntegrationAction] = []
    configSchema: dict = {}
    webhookUrlTemplate: Optional[str] = None
    docsUrl: Optional[str] = None
