"""Integration webhook endpoints + management API + Spotify/Calendar tools."""
import json
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Response, Query
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/integrations", tags=["integrations"])


# ── Pydantic models ──────────────────────────────────────────────────

class ConfigureRequest(BaseModel):
    config: dict
    user_label: str = ""


class SpotifySearchRequest(BaseModel):
    query: str
    type: str = "track"


class SpotifyQueueRequest(BaseModel):
    uri: str


class CalendarEventRequest(BaseModel):
    summary: str
    start: str
    end: str
    description: str = ""


class CalendarUpdateRequest(BaseModel):
    summary: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None


# ── Helpers ──────────────────────────────────────────────────────────

def _get_integration(platform: str) -> Optional[dict]:
    from services.memory_service import memory_service
    conn = memory_service._get_conn()
    row = conn.execute("SELECT * FROM integrations WHERE platform = ?", (platform,)).fetchone()
    return dict(row) if row else None


def _get_adapter_config(platform: str) -> dict:
    """Load adapter config from DB."""
    integration = _get_integration(platform)
    if not integration:
        return {}
    config_str = integration.get("config", "{}")
    if isinstance(config_str, str):
        try:
            return json.loads(config_str)
        except json.JSONDecodeError:
            return {}
    return config_str


# ── Webhook endpoints ────────────────────────────────────────────────

@router.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """Receive Telegram Bot updates."""
    from services.messaging_gateway import messaging_gateway
    body = await request.json()
    config = _get_adapter_config("telegram")
    if not config:
        raise HTTPException(400, "Telegram not configured")
    result = await messaging_gateway.handle_inbound("telegram", body, config)
    return result


@router.get("/whatsapp/webhook")
async def whatsapp_verify(request: Request):
    """WhatsApp verification challenge."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    config = _get_adapter_config("whatsapp")
    if mode == "subscribe" and token == config.get("verify_token"):
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(403, "Verification failed")


@router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    """Receive WhatsApp messages."""
    from services.messaging_gateway import messaging_gateway
    body = await request.json()
    config = _get_adapter_config("whatsapp")
    if not config:
        raise HTTPException(400, "WhatsApp not configured")
    result = await messaging_gateway.handle_inbound("whatsapp", body, config)
    return result


@router.post("/discord/webhook")
async def discord_webhook(request: Request):
    """Receive Discord interaction payloads."""
    body = await request.json()
    # Handle Discord PING verification
    if body.get("type") == 1:
        return {"type": 1}
    from services.messaging_gateway import messaging_gateway
    config = _get_adapter_config("discord")
    if not config:
        raise HTTPException(400, "Discord not configured")
    result = await messaging_gateway.handle_inbound("discord", body, config)
    return result


@router.post("/slack/webhook")
async def slack_webhook(request: Request):
    """Receive Slack Events API payloads."""
    body = await request.json()
    # Handle Slack URL verification
    if body.get("type") == "url_verification":
        return {"challenge": body.get("challenge", "")}
    from services.messaging_gateway import messaging_gateway
    config = _get_adapter_config("slack")
    if not config:
        raise HTTPException(400, "Slack not configured")
    result = await messaging_gateway.handle_inbound("slack", body, config)
    return result


@router.post("/gmail/webhook")
async def gmail_webhook(request: Request):
    """Receive Gmail Pub/Sub push notifications."""
    from services.messaging_gateway import messaging_gateway
    body = await request.json()
    config = _get_adapter_config("gmail")
    if not config:
        raise HTTPException(400, "Gmail not configured")
    result = await messaging_gateway.handle_inbound("gmail", body, config)
    return result


# ── Management endpoints ─────────────────────────────────────────────

@router.get("")
async def list_integrations():
    """List all integrations with status."""
    from services.memory_service import memory_service
    conn = memory_service._get_conn()
    rows = conn.execute("SELECT * FROM integrations ORDER BY platform").fetchall()
    result = []
    for row in rows:
        d = dict(row)
        # Don't expose full config with secrets
        config = json.loads(d.get("config", "{}")) if isinstance(d.get("config"), str) else d.get("config", {})
        d["config_keys"] = list(config.keys())
        d.pop("config", None)
        # Count messages
        count = conn.execute(
            "SELECT COUNT(*) FROM integration_messages WHERE integration_id = ?", (d["id"],)
        ).fetchone()[0]
        d["message_count"] = count
        result.append(d)

    # Add unconfigured platforms
    from services.platform_adapters import ADAPTERS
    configured = {r["platform"] for r in result}
    for platform in ADAPTERS:
        if platform not in configured:
            result.append({
                "id": None,
                "platform": platform,
                "enabled": False,
                "config_keys": [],
                "message_count": 0,
                "user_label": "",
            })

    return result


@router.post("/{platform}/configure")
async def configure_integration(platform: str, req: ConfigureRequest):
    """Save credentials for a platform."""
    from services.platform_adapters import ADAPTERS
    if platform not in ADAPTERS:
        raise HTTPException(400, f"Unknown platform: {platform}")

    from services.memory_service import memory_service
    conn = memory_service._get_conn()
    now = datetime.utcnow().isoformat()

    existing = _get_integration(platform)
    if existing:
        conn.execute(
            "UPDATE integrations SET config = ?, user_label = ?, updated_at = ? WHERE platform = ?",
            (json.dumps(req.config), req.user_label, now, platform),
        )
    else:
        conn.execute(
            "INSERT INTO integrations (id, platform, config, enabled, user_label, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), platform, json.dumps(req.config), True, req.user_label, now, now),
        )
    conn.commit()
    return {"configured": True, "platform": platform}


@router.post("/{platform}/test")
async def test_integration(platform: str):
    """Test connectivity for a configured platform."""
    from services.platform_adapters import get_adapter
    config = _get_adapter_config(platform)
    if not config:
        raise HTTPException(400, f"{platform} not configured")
    adapter = get_adapter(platform, config)
    result = await adapter.test_connection(config)
    return result


@router.post("/{platform}/enable")
async def enable_integration(platform: str):
    """Enable a configured integration."""
    from services.memory_service import memory_service
    conn = memory_service._get_conn()
    conn.execute(
        "UPDATE integrations SET enabled = 1, updated_at = ? WHERE platform = ?",
        (datetime.utcnow().isoformat(), platform),
    )
    conn.commit()
    return {"enabled": True}


@router.post("/{platform}/disable")
async def disable_integration(platform: str):
    """Disable an integration."""
    from services.memory_service import memory_service
    conn = memory_service._get_conn()
    conn.execute(
        "UPDATE integrations SET enabled = 0, updated_at = ? WHERE platform = ?",
        (datetime.utcnow().isoformat(), platform),
    )
    conn.commit()
    return {"enabled": False}


@router.delete("/{platform}")
async def delete_integration(platform: str):
    """Remove an integration."""
    from services.memory_service import memory_service
    conn = memory_service._get_conn()
    conn.execute("DELETE FROM integrations WHERE platform = ?", (platform,))
    conn.commit()
    return {"deleted": True}


@router.get("/{platform}/setup")
async def get_setup_instructions(platform: str):
    """Get setup instructions for a platform."""
    from services.platform_adapters import get_adapter
    adapter = get_adapter(platform)
    return adapter.get_setup_instructions()


# ── Spotify tool endpoints ───────────────────────────────────────────

@router.get("/spotify/now-playing")
async def spotify_now_playing():
    """Get currently playing track."""
    config = _get_adapter_config("spotify")
    if not config:
        raise HTTPException(400, "Spotify not configured")
    from services.platform_adapters import SpotifyAdapter
    adapter = SpotifyAdapter(**config)
    return await adapter.get_now_playing()


@router.post("/spotify/search")
async def spotify_search(req: SpotifySearchRequest):
    """Search Spotify."""
    config = _get_adapter_config("spotify")
    if not config:
        raise HTTPException(400, "Spotify not configured")
    from services.platform_adapters import SpotifyAdapter
    adapter = SpotifyAdapter(**config)
    return await adapter.search(req.query, req.type)


@router.post("/spotify/queue")
async def spotify_queue(req: SpotifyQueueRequest):
    """Add track to queue."""
    config = _get_adapter_config("spotify")
    if not config:
        raise HTTPException(400, "Spotify not configured")
    from services.platform_adapters import SpotifyAdapter
    adapter = SpotifyAdapter(**config)
    return await adapter.add_to_queue(req.uri)


@router.get("/spotify/playlists")
async def spotify_playlists():
    """List user playlists."""
    config = _get_adapter_config("spotify")
    if not config:
        raise HTTPException(400, "Spotify not configured")
    from services.platform_adapters import SpotifyAdapter
    adapter = SpotifyAdapter(**config)
    return await adapter.get_playlists()


# ── Calendar tool endpoints ──────────────────────────────────────────

@router.get("/calendar/events")
async def calendar_list_events(
    max_results: int = Query(10, le=50),
    time_min: Optional[str] = None,
):
    """List upcoming calendar events."""
    config = _get_adapter_config("calendar")
    if not config:
        raise HTTPException(400, "Calendar not configured")
    from services.platform_adapters import CalendarAdapter
    adapter = CalendarAdapter(credentials_json=json.dumps(config.get("credentials", config)))
    return await adapter.list_events(max_results, time_min)


@router.post("/calendar/events")
async def calendar_create_event(req: CalendarEventRequest):
    """Create a calendar event."""
    config = _get_adapter_config("calendar")
    if not config:
        raise HTTPException(400, "Calendar not configured")
    from services.platform_adapters import CalendarAdapter
    adapter = CalendarAdapter(credentials_json=json.dumps(config.get("credentials", config)))
    return await adapter.create_event(req.summary, req.start, req.end, req.description)


@router.put("/calendar/events/{event_id}")
async def calendar_update_event(event_id: str, req: CalendarUpdateRequest):
    """Update a calendar event."""
    config = _get_adapter_config("calendar")
    if not config:
        raise HTTPException(400, "Calendar not configured")
    from services.platform_adapters import CalendarAdapter
    adapter = CalendarAdapter(credentials_json=json.dumps(config.get("credentials", config)))
    update_fields = {k: v for k, v in req.dict().items() if v is not None}
    return await adapter.update_event(event_id, **update_fields)


@router.delete("/calendar/events/{event_id}")
async def calendar_delete_event(event_id: str):
    """Delete a calendar event."""
    config = _get_adapter_config("calendar")
    if not config:
        raise HTTPException(400, "Calendar not configured")
    from services.platform_adapters import CalendarAdapter
    adapter = CalendarAdapter(credentials_json=json.dumps(config.get("credentials", config)))
    return await adapter.delete_event(event_id)
