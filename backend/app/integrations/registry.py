"""
Integration Registry — first-class integration catalog.

Fully implemented (5+):
  - Slack
  - WhatsApp (via Twilio)
  - Stripe
  - Gmail
  - Webhook (generic)

Cleanly stubbed:
  - Twilio SMS, SendGrid, HubSpot, Salesforce, Jira, GitHub, PagerDuty,
    Zapier, Discord, Telegram, Shopify, Mailchimp, Zoom, Calendly
"""
from __future__ import annotations
from app.integrations.models import Integration, IntegrationTrigger, IntegrationAction
from app.models.schemas import AuthType

INTEGRATION_REGISTRY: dict[str, Integration] = {

    # ─────────────────────────────────────────────
    # FULLY IMPLEMENTED
    # ─────────────────────────────────────────────

    "slack": Integration(
        id="slack",
        displayName="Slack",
        description="Send messages, notifications, and alerts to Slack channels and users.",
        authType=AuthType.oauth2,
        category="messaging",
        logoColor="#4A154B",
        isFullyImplemented=True,
        triggers=[
            IntegrationTrigger(id="message_received", name="Message Received", description="Triggered when a message is sent in a channel"),
            IntegrationTrigger(id="mention", name="Bot Mentioned", description="Triggered when the bot is @mentioned"),
        ],
        actions=[
            IntegrationAction(id="send_message", name="Send Message", description="Send a message to a channel", requiredParams=["channel", "text"]),
            IntegrationAction(id="send_dm", name="Send Direct Message", description="Send a DM to a user", requiredParams=["user_id", "text"]),
            IntegrationAction(id="post_block", name="Post Block Message", description="Post rich block message", requiredParams=["channel", "blocks"]),
        ],
        configSchema={"bot_token": "string", "signing_secret": "string"},
        docsUrl="https://api.slack.com/",
    ),

    "whatsapp": Integration(
        id="whatsapp",
        displayName="WhatsApp",
        description="Send WhatsApp messages via Twilio or Meta Business API for customer notifications.",
        authType=AuthType.api_key,
        category="messaging",
        logoColor="#25D366",
        isFullyImplemented=True,
        triggers=[
            IntegrationTrigger(id="message_received", name="Message Received", description="Triggered when a WhatsApp message is received"),
        ],
        actions=[
            IntegrationAction(id="send_template_message", name="Send Template Message", description="Send approved WhatsApp template message", requiredParams=["to", "template_name", "params"]),
            IntegrationAction(id="send_text", name="Send Text Message", description="Send a plain text WhatsApp message", requiredParams=["to", "body"]),
            IntegrationAction(id="send_media", name="Send Media", description="Send image/document/video", requiredParams=["to", "media_url", "media_type"]),
        ],
        configSchema={"account_sid": "string", "auth_token": "string", "from_number": "string"},
        docsUrl="https://www.twilio.com/docs/whatsapp",
    ),

    "stripe": Integration(
        id="stripe",
        displayName="Stripe",
        description="Accept payments, manage subscriptions, invoicing, and billing operations.",
        authType=AuthType.api_key,
        category="payments",
        logoColor="#635BFF",
        isFullyImplemented=True,
        triggers=[
            IntegrationTrigger(id="payment_succeeded", name="Payment Succeeded", description="Triggered when a payment succeeds"),
            IntegrationTrigger(id="payment_failed", name="Payment Failed", description="Triggered when a payment fails"),
            IntegrationTrigger(id="subscription_created", name="Subscription Created", description="New subscription started"),
            IntegrationTrigger(id="subscription_cancelled", name="Subscription Cancelled", description="Subscription was cancelled"),
            IntegrationTrigger(id="invoice_paid", name="Invoice Paid", description="Invoice payment completed"),
        ],
        actions=[
            IntegrationAction(id="create_payment_intent", name="Create Payment Intent", description="Initialize a payment", requiredParams=["amount", "currency"]),
            IntegrationAction(id="create_subscription", name="Create Subscription", description="Start a subscription", requiredParams=["customer_id", "price_id"]),
            IntegrationAction(id="cancel_subscription", name="Cancel Subscription", description="Cancel a subscription", requiredParams=["subscription_id"]),
            IntegrationAction(id="create_customer", name="Create Customer", description="Create a Stripe customer", requiredParams=["email"]),
            IntegrationAction(id="refund_payment", name="Refund Payment", description="Issue a full or partial refund", requiredParams=["payment_intent_id"]),
        ],
        configSchema={"secret_key": "string", "publishable_key": "string", "webhook_secret": "string"},
        docsUrl="https://stripe.com/docs",
    ),

    "gmail": Integration(
        id="gmail",
        displayName="Gmail",
        description="Send transactional and marketing emails via Gmail API.",
        authType=AuthType.oauth2,
        category="email",
        logoColor="#EA4335",
        isFullyImplemented=True,
        triggers=[
            IntegrationTrigger(id="email_received", name="Email Received", description="Triggered when an email is received"),
            IntegrationTrigger(id="email_opened", name="Email Opened", description="Triggered when recipient opens the email"),
        ],
        actions=[
            IntegrationAction(id="send_email", name="Send Email", description="Send an email", requiredParams=["to", "subject", "body"]),
            IntegrationAction(id="send_html_email", name="Send HTML Email", description="Send HTML-formatted email", requiredParams=["to", "subject", "html_body"]),
            IntegrationAction(id="send_with_attachment", name="Send with Attachment", description="Send email with file attachment", requiredParams=["to", "subject", "body", "attachment_url"]),
        ],
        configSchema={"client_id": "string", "client_secret": "string", "refresh_token": "string"},
        docsUrl="https://developers.google.com/gmail/api",
    ),

    "webhook": Integration(
        id="webhook",
        displayName="Webhook",
        description="Send HTTP POST requests to any external URL on pipeline events.",
        authType=AuthType.none,
        category="generic",
        logoColor="#6366F1",
        isFullyImplemented=True,
        triggers=[
            IntegrationTrigger(id="http_received", name="HTTP Request Received", description="Triggered on incoming POST request"),
        ],
        actions=[
            IntegrationAction(id="post_json", name="POST JSON Payload", description="Send JSON payload to webhook URL", requiredParams=["url", "payload"]),
            IntegrationAction(id="post_with_auth", name="POST with Auth Header", description="Send authenticated request", requiredParams=["url", "payload", "auth_header"]),
        ],
        configSchema={"url": "string", "secret": "string", "headers": "object"},
        webhookUrlTemplate="https://hooks.example.com/webhook/{id}",
        docsUrl=None,
    ),

    # ─────────────────────────────────────────────
    # CLEANLY STUBBED
    # ─────────────────────────────────────────────

    "twilio": Integration(
        id="twilio",
        displayName="Twilio SMS",
        description="Send SMS messages via Twilio programmable messaging.",
        authType=AuthType.api_key,
        category="messaging",
        logoColor="#F22F46",
        isFullyImplemented=False,
        actions=[IntegrationAction(id="send_sms", name="Send SMS", description="Send an SMS message", requiredParams=["to", "body"])],
        configSchema={"account_sid": "string", "auth_token": "string"},
    ),

    "sendgrid": Integration(
        id="sendgrid",
        displayName="SendGrid",
        description="Transactional and marketing email delivery via SendGrid.",
        authType=AuthType.api_key,
        category="email",
        logoColor="#1A82E2",
        isFullyImplemented=False,
        actions=[IntegrationAction(id="send_email", name="Send Email", description="Send transactional email", requiredParams=["to", "subject", "body"])],
        configSchema={"api_key": "string"},
    ),

    "hubspot": Integration(
        id="hubspot",
        displayName="HubSpot",
        description="CRM automation, contact management, and deal tracking.",
        authType=AuthType.oauth2,
        category="crm",
        logoColor="#FF7A59",
        isFullyImplemented=False,
        actions=[
            IntegrationAction(id="create_contact", name="Create Contact", description="Add a contact to HubSpot", requiredParams=["email"]),
            IntegrationAction(id="update_deal", name="Update Deal", description="Update a deal stage", requiredParams=["deal_id", "stage"]),
        ],
        configSchema={"api_key": "string"},
    ),

    "salesforce": Integration(
        id="salesforce",
        displayName="Salesforce",
        description="Enterprise CRM integration for leads, opportunities, and accounts.",
        authType=AuthType.oauth2,
        category="crm",
        logoColor="#00A1E0",
        isFullyImplemented=False,
        actions=[
            IntegrationAction(id="create_lead", name="Create Lead", description="Create a lead in Salesforce", requiredParams=["first_name", "last_name", "email"]),
        ],
        configSchema={"client_id": "string", "client_secret": "string", "instance_url": "string"},
    ),

    "jira": Integration(
        id="jira",
        displayName="Jira",
        description="Create and update Jira issues, sprints, and project tracking.",
        authType=AuthType.api_key,
        category="devops",
        logoColor="#0052CC",
        isFullyImplemented=False,
        actions=[
            IntegrationAction(id="create_issue", name="Create Issue", description="Create a Jira issue", requiredParams=["project_key", "summary", "issue_type"]),
        ],
        configSchema={"domain": "string", "email": "string", "api_token": "string"},
    ),

    "github": Integration(
        id="github",
        displayName="GitHub",
        description="GitHub webhooks, issue tracking, and repository automation.",
        authType=AuthType.oauth2,
        category="devops",
        logoColor="#24292E",
        isFullyImplemented=False,
        actions=[
            IntegrationAction(id="create_issue", name="Create Issue", description="Create a GitHub issue", requiredParams=["repo", "title"]),
        ],
        configSchema={"personal_access_token": "string"},
    ),

    "pagerduty": Integration(
        id="pagerduty",
        displayName="PagerDuty",
        description="Incident management, alerting, and on-call scheduling.",
        authType=AuthType.api_key,
        category="devops",
        logoColor="#06AC38",
        isFullyImplemented=False,
        actions=[
            IntegrationAction(id="trigger_incident", name="Trigger Incident", description="Create a PagerDuty incident", requiredParams=["service_key", "description"]),
        ],
        configSchema={"api_key": "string", "service_key": "string"},
    ),

    "zapier": Integration(
        id="zapier",
        displayName="Zapier",
        description="Connect 5000+ apps via Zapier webhooks and automation.",
        authType=AuthType.webhook,
        category="generic",
        logoColor="#FF4A00",
        isFullyImplemented=False,
        actions=[
            IntegrationAction(id="trigger_zap", name="Trigger Zap", description="Send data to Zapier webhook", requiredParams=["webhook_url", "payload"]),
        ],
        configSchema={"webhook_url": "string"},
    ),

    "discord": Integration(
        id="discord",
        displayName="Discord",
        description="Send messages and notifications to Discord channels via webhooks.",
        authType=AuthType.webhook,
        category="messaging",
        logoColor="#5865F2",
        isFullyImplemented=False,
        actions=[
            IntegrationAction(id="send_message", name="Send Message", description="Post a message to Discord", requiredParams=["webhook_url", "content"]),
        ],
        configSchema={"webhook_url": "string"},
    ),

    "shopify": Integration(
        id="shopify",
        displayName="Shopify",
        description="E-commerce order management, product sync, and customer data.",
        authType=AuthType.api_key,
        category="payments",
        logoColor="#96BF48",
        isFullyImplemented=False,
        actions=[
            IntegrationAction(id="get_order", name="Get Order", description="Fetch order details", requiredParams=["order_id"]),
        ],
        configSchema={"shop_domain": "string", "api_key": "string", "api_secret": "string"},
    ),
}


def get_integration(integration_id: str) -> Integration | None:
    """Fetch a single integration by ID."""
    return INTEGRATION_REGISTRY.get(integration_id.lower())


def list_integrations() -> list[Integration]:
    """Return all integrations as a list."""
    return list(INTEGRATION_REGISTRY.values())


def get_implemented_integrations() -> list[Integration]:
    """Return only fully implemented integrations."""
    return [i for i in INTEGRATION_REGISTRY.values() if i.isFullyImplemented]
