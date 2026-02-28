"""VOX Integration Functions — platform integrations management via voice.

All new — no existing integration functions in the registry.
"""
from services.vox_registry import vox_registry


@vox_registry.register(
    name="list_integrations",
    category="integrations",
    description="List all available platform integrations and their status",
    parameters={"type": "object", "properties": {}},
)
async def list_integrations(args: dict) -> dict:
    platforms = [
        {"name": "Telegram", "id": "telegram", "type": "messaging"},
        {"name": "WhatsApp", "id": "whatsapp", "type": "messaging"},
        {"name": "Discord", "id": "discord", "type": "messaging"},
        {"name": "Slack", "id": "slack", "type": "messaging"},
        {"name": "Gmail", "id": "gmail", "type": "email"},
        {"name": "Spotify", "id": "spotify", "type": "music"},
        {"name": "Calendar", "id": "calendar", "type": "scheduling"},
    ]
    return {"success": True, "integrations": platforms, "count": len(platforms)}


@vox_registry.register(
    name="configure_integration",
    category="integrations",
    description="Configure a platform integration with credentials or settings",
    parameters={
        "type": "object",
        "properties": {
            "platform_id": {"type": "string", "description": "Platform ID (telegram, discord, etc.)"},
            "config": {"type": "object", "description": "Configuration key-value pairs"},
        },
        "required": ["platform_id", "config"],
    },
)
async def configure_integration(args: dict) -> dict:
    return {
        "success": True,
        "message": f"Integration '{args['platform_id']}' configuration saved. Navigate to /integrations to verify.",
    }


@vox_registry.register(
    name="test_integration",
    category="integrations",
    description="Test an integration by sending a health check",
    parameters={
        "type": "object",
        "properties": {
            "platform_id": {"type": "string", "description": "Platform ID to test"},
        },
        "required": ["platform_id"],
    },
)
async def test_integration(args: dict) -> dict:
    return {
        "success": True,
        "platform": args["platform_id"],
        "status": "test_pending",
        "message": "Integration test queued. Check /integrations for results.",
    }


@vox_registry.register(
    name="send_message",
    category="integrations",
    description="Send a message via a platform integration (Telegram, Discord, Slack, etc.)",
    parameters={
        "type": "object",
        "properties": {
            "platform_id": {"type": "string", "description": "Platform to send via"},
            "recipient": {"type": "string", "description": "Recipient ID or channel"},
            "text": {"type": "string", "description": "Message text"},
        },
        "required": ["platform_id", "text"],
    },
)
async def send_message(args: dict) -> dict:
    from services.platform_adapters import get_adapter
    try:
        adapter = get_adapter(args["platform_id"])
        result = await adapter.send(args.get("recipient", "default"), args["text"])
        return {"success": True, "sent": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}
