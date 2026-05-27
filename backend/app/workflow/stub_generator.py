"""
Workflow Stub Generator

Generates automation workflow stubs from:
  - integrations_requested in AppIntent
  - Entity names from DataSchema

Example output for "whatsapp" with "Deal" entity:
  {
    "name": "Notify via WhatsApp on Deal Close",
    "triggerEntity": "Deal",
    "triggerEvent": "status_changed",
    "integration": "whatsapp",
    "action": "send_template_message",
    "payloadSchema": {...},
    "fieldMappings": {...}
  }
"""
from __future__ import annotations
import logging
from app.models.schemas import AppIntent, DataSchema, WorkflowStub
from app.integrations.registry import INTEGRATION_REGISTRY, get_integration

logger = logging.getLogger(__name__)

# Default trigger event mappings per entity for common domain patterns
DEFAULT_TRIGGER_EVENTS: dict[str, list[str]] = {
    "deal":        ["status_changed", "created"],
    "order":       ["created", "status_changed", "payment_completed"],
    "payment":     ["completed", "failed"],
    "invoice":     ["paid", "overdue"],
    "lead":        ["created", "assigned", "status_changed"],
    "user":        ["created", "verified"],
    "appointment": ["created", "cancelled", "reminder"],
    "booking":     ["confirmed", "cancelled"],
    "ticket":      ["created", "resolved", "escalated"],
    "subscription":["created", "cancelled", "renewed"],
}

# Action templates per integration × trigger event
WORKFLOW_TEMPLATES: dict[str, dict[str, dict]] = {
    "slack": {
        "default": {
            "action": "send_message",
            "payloadSchema": {
                "channel": "string",
                "text": "string",
            },
            "fieldMappings": {
                "text": "{{entity.name}} event: {{event}}",
                "channel": "#notifications",
            },
        }
    },
    "whatsapp": {
        "status_changed": {
            "action": "send_template_message",
            "payloadSchema": {
                "to": "string (phone number)",
                "template_name": "string",
                "params": "object",
            },
            "fieldMappings": {
                "to": "{{entity.phone}}",
                "template_name": "status_update",
                "params.entity_id": "{{entity.id}}",
                "params.status": "{{entity.status}}",
            },
        },
        "created": {
            "action": "send_template_message",
            "payloadSchema": {
                "to": "string (phone number)",
                "template_name": "string",
                "params": "object",
            },
            "fieldMappings": {
                "to": "{{entity.phone}}",
                "template_name": "new_record_created",
                "params.entity_name": "{{entity.name}}",
            },
        },
        "default": {
            "action": "send_text",
            "payloadSchema": {"to": "string", "body": "string"},
            "fieldMappings": {"to": "{{entity.phone}}", "body": "Update: {{entity.id}} - {{event}}"},
        },
    },
    "stripe": {
        "payment_completed": {
            "action": "create_payment_intent",
            "payloadSchema": {"amount": "integer (cents)", "currency": "string"},
            "fieldMappings": {"amount": "{{entity.amount}}", "currency": "{{entity.currency}}"},
        },
        "default": {
            "action": "create_customer",
            "payloadSchema": {"email": "string"},
            "fieldMappings": {"email": "{{entity.email}}"},
        },
    },
    "gmail": {
        "created": {
            "action": "send_email",
            "payloadSchema": {"to": "string", "subject": "string", "body": "string"},
            "fieldMappings": {
                "to": "{{entity.email}}",
                "subject": "New {{entity_name}} Created",
                "body": "Dear user, your {{entity_name}} has been successfully created.",
            },
        },
        "default": {
            "action": "send_html_email",
            "payloadSchema": {"to": "string", "subject": "string", "html_body": "string"},
            "fieldMappings": {
                "to": "{{entity.email}}",
                "subject": "Update: {{entity_name}} {{event}}",
                "html_body": "<p>Update for {{entity_name}}: {{event}}</p>",
            },
        },
    },
    "webhook": {
        "default": {
            "action": "post_json",
            "payloadSchema": {"url": "string", "payload": "object"},
            "fieldMappings": {
                "url": "{{webhook_url}}",
                "payload.entity_id": "{{entity.id}}",
                "payload.event": "{{event}}",
                "payload.timestamp": "{{now}}",
            },
        }
    },
}


def generate_workflow_stubs(intent: AppIntent, data_schema: DataSchema) -> list[WorkflowStub]:
    """
    Generate workflow stubs for all requested integrations × relevant entities.
    """
    stubs: list[WorkflowStub] = []
    entity_names = [e.name for e in data_schema.entities]

    for integration_id in intent.integrations_requested:
        integration_id = integration_id.lower()
        integration = get_integration(integration_id)

        if not integration:
            logger.warning(f"[Workflow] Unknown integration '{integration_id}' — skipping stub generation")
            continue

        # Find the best entity to pair with this integration
        target_entities = _pick_relevant_entities(integration_id, entity_names)

        for entity_name in target_entities[:2]:  # Max 2 stubs per integration
            trigger_event = _pick_trigger_event(integration_id, entity_name)
            template = _get_template(integration_id, trigger_event)

            stub = WorkflowStub(
                name=f"{_humanize(trigger_event)} → {integration.displayName} ({entity_name})",
                triggerEntity=entity_name,
                triggerEvent=trigger_event,
                integration=integration_id,
                action=template["action"],
                payloadSchema=template["payloadSchema"],
                fieldMappings=template["fieldMappings"],
                actionMetadata={
                    "integration_display": integration.displayName,
                    "integration_category": integration.category,
                    "auth_type": integration.authType.value,
                    "description": f"Automatically triggered when {entity_name} {trigger_event}",
                },
            )
            stubs.append(stub)
            logger.info(f"[Workflow] Generated stub: {stub.name}")

    return stubs


def _pick_relevant_entities(integration_id: str, entity_names: list[str]) -> list[str]:
    """Pick the most relevant entities for a given integration."""
    # Integration-specific entity preferences
    preferences: dict[str, list[str]] = {
        "stripe":    ["Order", "Payment", "Subscription", "Invoice", "Deal"],
        "whatsapp":  ["Deal", "Lead", "Order", "Appointment", "Booking", "User"],
        "gmail":     ["User", "Lead", "Order", "Contact", "Subscription"],
        "slack":     ["Deal", "Order", "Ticket", "Lead", "Alert", "Incident"],
        "webhook":   entity_names,  # Any entity
    }
    preferred = preferences.get(integration_id, entity_names)

    result = []
    # First pass: preferred entities that exist
    for pref in preferred:
        for name in entity_names:
            if name.lower() == pref.lower() and name not in result:
                result.append(name)
                break

    # Second pass: fill with any remaining entities
    for name in entity_names:
        if name not in result and name != "User":
            result.append(name)

    return result


def _pick_trigger_event(integration_id: str, entity_name: str) -> str:
    """Pick the most appropriate trigger event."""
    entity_key = entity_name.lower()
    events = DEFAULT_TRIGGER_EVENTS.get(entity_key, ["created", "updated"])

    # Integration-specific event preferences
    if integration_id == "stripe" and "payment" in entity_key:
        return "payment_completed"
    if integration_id == "whatsapp" and ("deal" in entity_key or "order" in entity_key):
        return "status_changed"

    return events[0]


def _get_template(integration_id: str, trigger_event: str) -> dict:
    """Get the workflow template for an integration × event."""
    integration_templates = WORKFLOW_TEMPLATES.get(integration_id, WORKFLOW_TEMPLATES["webhook"])
    return integration_templates.get(trigger_event, integration_templates.get("default", {
        "action": "send_notification",
        "payloadSchema": {"payload": "object"},
        "fieldMappings": {"payload.entity_id": "{{entity.id}}"},
    }))


def _humanize(event: str) -> str:
    """Convert snake_case event to human-readable."""
    return event.replace("_", " ").title()
