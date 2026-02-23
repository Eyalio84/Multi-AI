"""Abstract base + 7 concrete platform adapters for messaging gateway."""
import hashlib
import hmac
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class NormalizedMessage:
    """Platform-agnostic inbound message."""
    platform: str
    sender_id: str
    sender_name: str
    text: str
    chat_id: str
    platform_message_id: str = ""
    attachments: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class PlatformAdapter(ABC):
    """Base class for all platform adapters."""

    platform_name: str = "unknown"

    @abstractmethod
    def validate_webhook(self, headers: dict, body: bytes) -> bool:
        """Validate incoming webhook signature."""
        ...

    @abstractmethod
    def parse_inbound(self, payload: dict) -> Optional[NormalizedMessage]:
        """Parse platform-specific payload into NormalizedMessage."""
        ...

    @abstractmethod
    async def send_response(self, recipient_id: str, text: str, attachments: list[dict] = None) -> dict:
        """Send response back to the platform."""
        ...

    @abstractmethod
    def get_setup_instructions(self) -> dict:
        """Return setup instructions for this platform."""
        ...

    @abstractmethod
    async def test_connection(self, config: dict) -> dict:
        """Test if credentials are valid."""
        ...


class TelegramAdapter(PlatformAdapter):
    """Telegram Bot API adapter."""

    platform_name = "telegram"

    def __init__(self, bot_token: str = ""):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}" if bot_token else ""

    def validate_webhook(self, headers: dict, body: bytes) -> bool:
        # Telegram doesn't sign webhooks, but we can verify the token is set
        return bool(self.bot_token)

    def parse_inbound(self, payload: dict) -> Optional[NormalizedMessage]:
        msg = payload.get("message") or payload.get("edited_message")
        if not msg:
            return None
        text = msg.get("text", "")
        if not text:
            return None
        from_user = msg.get("from", {})
        return NormalizedMessage(
            platform="telegram",
            sender_id=str(from_user.get("id", "")),
            sender_name=from_user.get("first_name", "") + " " + from_user.get("last_name", ""),
            text=text,
            chat_id=str(msg.get("chat", {}).get("id", "")),
            platform_message_id=str(msg.get("message_id", "")),
        )

    async def send_response(self, recipient_id: str, text: str, attachments: list[dict] = None) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/sendMessage",
                json={"chat_id": recipient_id, "text": text, "parse_mode": "Markdown"},
                timeout=30,
            )
            return resp.json()

    async def test_connection(self, config: dict) -> dict:
        token = config.get("bot_token", self.bot_token)
        if not token:
            return {"ok": False, "error": "No bot token configured"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
            data = resp.json()
            if data.get("ok"):
                return {"ok": True, "bot_name": data["result"].get("username", "")}
            return {"ok": False, "error": data.get("description", "Unknown error")}

    def get_setup_instructions(self) -> dict:
        return {
            "platform": "telegram",
            "steps": [
                "1. Message @BotFather on Telegram",
                "2. Send /newbot and follow the prompts",
                "3. Copy the bot token",
                "4. Set webhook: POST https://api.telegram.org/bot<TOKEN>/setWebhook?url=<YOUR_URL>/api/integrations/telegram/webhook",
            ],
            "required_fields": ["bot_token"],
        }


class WhatsAppAdapter(PlatformAdapter):
    """WhatsApp Cloud API adapter."""

    platform_name = "whatsapp"

    def __init__(self, token: str = "", phone_id: str = "", verify_token: str = ""):
        self.token = token
        self.phone_id = phone_id
        self.verify_token = verify_token

    def validate_webhook(self, headers: dict, body: bytes) -> bool:
        return bool(self.token)

    def parse_inbound(self, payload: dict) -> Optional[NormalizedMessage]:
        try:
            entry = payload.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])
            if not messages:
                return None
            msg = messages[0]
            contact = value.get("contacts", [{}])[0]
            return NormalizedMessage(
                platform="whatsapp",
                sender_id=msg.get("from", ""),
                sender_name=contact.get("profile", {}).get("name", ""),
                text=msg.get("text", {}).get("body", ""),
                chat_id=msg.get("from", ""),
                platform_message_id=msg.get("id", ""),
            )
        except (IndexError, KeyError):
            return None

    async def send_response(self, recipient_id: str, text: str, attachments: list[dict] = None) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://graph.facebook.com/v18.0/{self.phone_id}/messages",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "messaging_product": "whatsapp",
                    "to": recipient_id,
                    "text": {"body": text},
                },
                timeout=30,
            )
            return resp.json()

    async def test_connection(self, config: dict) -> dict:
        token = config.get("token", self.token)
        phone_id = config.get("phone_id", self.phone_id)
        if not token or not phone_id:
            return {"ok": False, "error": "Missing token or phone_id"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://graph.facebook.com/v18.0/{phone_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            if resp.status_code == 200:
                return {"ok": True, "phone_id": phone_id}
            return {"ok": False, "error": resp.text[:200]}

    def get_setup_instructions(self) -> dict:
        return {
            "platform": "whatsapp",
            "steps": [
                "1. Go to Meta for Developers → WhatsApp → Getting Started",
                "2. Create a WhatsApp Business app",
                "3. Get your Phone Number ID and permanent token",
                "4. Configure webhook URL: <YOUR_URL>/api/integrations/whatsapp/webhook",
                "5. Set verify token to match your configuration",
            ],
            "required_fields": ["token", "phone_id", "verify_token"],
        }


class DiscordAdapter(PlatformAdapter):
    """Discord webhook interactions adapter."""

    platform_name = "discord"

    def __init__(self, public_key: str = "", bot_token: str = ""):
        self.public_key = public_key
        self.bot_token = bot_token

    def validate_webhook(self, headers: dict, body: bytes) -> bool:
        signature = headers.get("x-signature-ed25519", "")
        timestamp = headers.get("x-signature-timestamp", "")
        if not signature or not timestamp or not self.public_key:
            return False
        try:
            from hashlib import sha512
            message = timestamp.encode() + body
            # Ed25519 verification would go here; simplified for now
            return bool(self.public_key)
        except Exception:
            return False

    def parse_inbound(self, payload: dict) -> Optional[NormalizedMessage]:
        # Interaction type 2 = APPLICATION_COMMAND
        if payload.get("type") == 2:
            data = payload.get("data", {})
            options = data.get("options", [])
            text = " ".join(o.get("value", "") for o in options if o.get("value"))
            user = payload.get("member", {}).get("user", {}) or payload.get("user", {})
            return NormalizedMessage(
                platform="discord",
                sender_id=user.get("id", ""),
                sender_name=user.get("username", ""),
                text=text or data.get("name", ""),
                chat_id=payload.get("channel_id", ""),
                platform_message_id=payload.get("id", ""),
            )
        return None

    async def send_response(self, recipient_id: str, text: str, attachments: list[dict] = None) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://discord.com/api/v10/channels/{recipient_id}/messages",
                headers={"Authorization": f"Bot {self.bot_token}"},
                json={"content": text[:2000]},
                timeout=30,
            )
            return resp.json()

    async def test_connection(self, config: dict) -> dict:
        token = config.get("bot_token", self.bot_token)
        if not token:
            return {"ok": False, "error": "No bot token configured"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://discord.com/api/v10/users/@me",
                headers={"Authorization": f"Bot {token}"},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {"ok": True, "bot_name": data.get("username", "")}
            return {"ok": False, "error": resp.text[:200]}

    def get_setup_instructions(self) -> dict:
        return {
            "platform": "discord",
            "steps": [
                "1. Go to Discord Developer Portal → Applications → New Application",
                "2. Copy Application ID and Public Key",
                "3. Go to Bot section → Create Bot → Copy Token",
                "4. Set Interactions Endpoint URL: <YOUR_URL>/api/integrations/discord/webhook",
                "5. Invite bot to your server with appropriate permissions",
            ],
            "required_fields": ["public_key", "bot_token"],
        }


class SlackAdapter(PlatformAdapter):
    """Slack Events API adapter."""

    platform_name = "slack"

    def __init__(self, bot_token: str = "", signing_secret: str = ""):
        self.bot_token = bot_token
        self.signing_secret = signing_secret

    def validate_webhook(self, headers: dict, body: bytes) -> bool:
        if not self.signing_secret:
            return False
        timestamp = headers.get("x-slack-request-timestamp", "")
        signature = headers.get("x-slack-signature", "")
        if not timestamp or not signature:
            return False
        # Check timestamp not too old (5 min)
        if abs(time.time() - int(timestamp)) > 300:
            return False
        sig_basestring = f"v0:{timestamp}:{body.decode()}"
        computed = "v0=" + hmac.new(
            self.signing_secret.encode(), sig_basestring.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(computed, signature)

    def parse_inbound(self, payload: dict) -> Optional[NormalizedMessage]:
        event = payload.get("event", {})
        if event.get("type") != "message" or event.get("subtype"):
            return None
        if event.get("bot_id"):
            return None  # Ignore bot messages
        return NormalizedMessage(
            platform="slack",
            sender_id=event.get("user", ""),
            sender_name=event.get("user", ""),
            text=event.get("text", ""),
            chat_id=event.get("channel", ""),
            platform_message_id=event.get("ts", ""),
        )

    async def send_response(self, recipient_id: str, text: str, attachments: list[dict] = None) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {self.bot_token}"},
                json={"channel": recipient_id, "text": text},
                timeout=30,
            )
            return resp.json()

    async def test_connection(self, config: dict) -> dict:
        token = config.get("bot_token", self.bot_token)
        if not token:
            return {"ok": False, "error": "No bot token configured"}
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://slack.com/api/auth.test",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            data = resp.json()
            if data.get("ok"):
                return {"ok": True, "team": data.get("team", ""), "user": data.get("user", "")}
            return {"ok": False, "error": data.get("error", "Unknown error")}

    def get_setup_instructions(self) -> dict:
        return {
            "platform": "slack",
            "steps": [
                "1. Go to api.slack.com/apps → Create New App",
                "2. Enable Event Subscriptions, set URL: <YOUR_URL>/api/integrations/slack/webhook",
                "3. Subscribe to 'message.channels' and 'message.im' events",
                "4. Install app to workspace",
                "5. Copy Bot User OAuth Token and Signing Secret",
            ],
            "required_fields": ["bot_token", "signing_secret"],
        }


class GmailAdapter(PlatformAdapter):
    """Gmail API adapter via Google Pub/Sub push notifications."""

    platform_name = "gmail"

    def __init__(self, client_id: str = "", client_secret: str = "", refresh_token: str = ""):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self._access_token: str = ""
        self._token_expiry: float = 0

    async def _get_access_token(self) -> str:
        if self._access_token and time.time() < self._token_expiry:
            return self._access_token
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token",
                },
                timeout=10,
            )
            data = resp.json()
            self._access_token = data.get("access_token", "")
            self._token_expiry = time.time() + data.get("expires_in", 3600) - 60
            return self._access_token

    def validate_webhook(self, headers: dict, body: bytes) -> bool:
        return bool(self.refresh_token)

    def parse_inbound(self, payload: dict) -> Optional[NormalizedMessage]:
        # Gmail Pub/Sub sends notification; we need to fetch the actual message
        message = payload.get("message", {})
        data = message.get("data", "")
        if not data:
            return None
        import base64
        try:
            decoded = json.loads(base64.b64decode(data))
            return NormalizedMessage(
                platform="gmail",
                sender_id=decoded.get("emailAddress", ""),
                sender_name=decoded.get("emailAddress", ""),
                text=f"New email notification from {decoded.get('emailAddress', 'unknown')}",
                chat_id=decoded.get("emailAddress", ""),
                platform_message_id=str(decoded.get("historyId", "")),
            )
        except Exception:
            return None

    async def send_response(self, recipient_id: str, text: str, attachments: list[dict] = None) -> dict:
        import base64
        token = await self._get_access_token()
        # Compose raw email
        raw_msg = f"To: {recipient_id}\r\nSubject: AI Workspace Reply\r\nContent-Type: text/plain\r\n\r\n{text}"
        encoded = base64.urlsafe_b64encode(raw_msg.encode()).decode()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                headers={"Authorization": f"Bearer {token}"},
                json={"raw": encoded},
                timeout=30,
            )
            return resp.json()

    async def test_connection(self, config: dict) -> dict:
        try:
            self.client_id = config.get("client_id", self.client_id)
            self.client_secret = config.get("client_secret", self.client_secret)
            self.refresh_token = config.get("refresh_token", self.refresh_token)
            token = await self._get_access_token()
            if token:
                return {"ok": True}
            return {"ok": False, "error": "Could not get access token"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_setup_instructions(self) -> dict:
        return {
            "platform": "gmail",
            "steps": [
                "1. Create OAuth2 credentials in Google Cloud Console",
                "2. Enable Gmail API",
                "3. Get refresh token via OAuth2 flow",
                "4. Set up Pub/Sub topic and subscription for push notifications",
                "5. Configure webhook URL: <YOUR_URL>/api/integrations/gmail/webhook",
            ],
            "required_fields": ["client_id", "client_secret", "refresh_token"],
        }


class SpotifyAdapter(PlatformAdapter):
    """Spotify Web API adapter — tool-based, not messaging."""

    platform_name = "spotify"

    def __init__(self, client_id: str = "", client_secret: str = "", refresh_token: str = ""):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self._access_token: str = ""
        self._token_expiry: float = 0

    async def _get_access_token(self) -> str:
        if self._access_token and time.time() < self._token_expiry:
            return self._access_token
        import base64
        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://accounts.spotify.com/api/token",
                headers={"Authorization": f"Basic {auth}"},
                data={"grant_type": "refresh_token", "refresh_token": self.refresh_token},
                timeout=10,
            )
            data = resp.json()
            self._access_token = data.get("access_token", "")
            self._token_expiry = time.time() + data.get("expires_in", 3600) - 60
            return self._access_token

    def validate_webhook(self, headers: dict, body: bytes) -> bool:
        return True  # Tool-based, no webhooks

    def parse_inbound(self, payload: dict) -> Optional[NormalizedMessage]:
        return None  # Tool-based, no inbound messages

    async def send_response(self, recipient_id: str, text: str, attachments: list[dict] = None) -> dict:
        return {}  # Tool-based, no messaging

    async def search(self, query: str, search_type: str = "track") -> dict:
        token = await self._get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.spotify.com/v1/search",
                params={"q": query, "type": search_type, "limit": 5},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            return resp.json()

    async def get_now_playing(self) -> dict:
        token = await self._get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.spotify.com/v1/me/player/currently-playing",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            if resp.status_code == 204:
                return {"is_playing": False}
            return resp.json()

    async def add_to_queue(self, uri: str) -> dict:
        token = await self._get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.spotify.com/v1/me/player/queue",
                params={"uri": uri},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            return {"queued": resp.status_code == 204}

    async def get_playlists(self) -> dict:
        token = await self._get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.spotify.com/v1/me/playlists",
                params={"limit": 20},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            return resp.json()

    async def test_connection(self, config: dict) -> dict:
        try:
            self.client_id = config.get("client_id", self.client_id)
            self.client_secret = config.get("client_secret", self.client_secret)
            self.refresh_token = config.get("refresh_token", self.refresh_token)
            token = await self._get_access_token()
            if token:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        "https://api.spotify.com/v1/me",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        return {"ok": True, "user": data.get("display_name", "")}
            return {"ok": False, "error": "Could not authenticate"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_setup_instructions(self) -> dict:
        return {
            "platform": "spotify",
            "steps": [
                "1. Go to developer.spotify.com/dashboard → Create App",
                "2. Set redirect URI to http://localhost:8888/callback",
                "3. Copy Client ID and Client Secret",
                "4. Get refresh token via OAuth2 PKCE flow",
                "5. Required scopes: user-read-playback-state, user-modify-playback-state, playlist-read-private",
            ],
            "required_fields": ["client_id", "client_secret", "refresh_token"],
        }


class CalendarAdapter(PlatformAdapter):
    """Google Calendar API adapter — tool-based."""

    platform_name = "calendar"

    def __init__(self, credentials_json: str = ""):
        self.credentials_json = credentials_json
        self._access_token: str = ""
        self._token_expiry: float = 0
        self._creds: dict = {}
        if credentials_json:
            try:
                self._creds = json.loads(credentials_json)
            except json.JSONDecodeError:
                pass

    async def _get_access_token(self) -> str:
        if self._access_token and time.time() < self._token_expiry:
            return self._access_token
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self._creds.get("client_id", ""),
                    "client_secret": self._creds.get("client_secret", ""),
                    "refresh_token": self._creds.get("refresh_token", ""),
                    "grant_type": "refresh_token",
                },
                timeout=10,
            )
            data = resp.json()
            self._access_token = data.get("access_token", "")
            self._token_expiry = time.time() + data.get("expires_in", 3600) - 60
            return self._access_token

    def validate_webhook(self, headers: dict, body: bytes) -> bool:
        return True

    def parse_inbound(self, payload: dict) -> Optional[NormalizedMessage]:
        return None  # Tool-based

    async def send_response(self, recipient_id: str, text: str, attachments: list[dict] = None) -> dict:
        return {}

    async def list_events(self, max_results: int = 10, time_min: str = None) -> dict:
        from datetime import datetime
        token = await self._get_access_token()
        params = {
            "maxResults": max_results,
            "singleEvents": "true",
            "orderBy": "startTime",
            "timeMin": time_min or datetime.utcnow().isoformat() + "Z",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                params=params,
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            return resp.json()

    async def create_event(self, summary: str, start: str, end: str, description: str = "") -> dict:
        token = await self._get_access_token()
        event = {
            "summary": summary,
            "start": {"dateTime": start, "timeZone": "UTC"},
            "end": {"dateTime": end, "timeZone": "UTC"},
        }
        if description:
            event["description"] = description
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                headers={"Authorization": f"Bearer {token}"},
                json=event,
                timeout=10,
            )
            return resp.json()

    async def update_event(self, event_id: str, **kwargs) -> dict:
        token = await self._get_access_token()
        update = {}
        if "summary" in kwargs:
            update["summary"] = kwargs["summary"]
        if "start" in kwargs:
            update["start"] = {"dateTime": kwargs["start"], "timeZone": "UTC"}
        if "end" in kwargs:
            update["end"] = {"dateTime": kwargs["end"], "timeZone": "UTC"}
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}",
                headers={"Authorization": f"Bearer {token}"},
                json=update,
                timeout=10,
            )
            return resp.json()

    async def delete_event(self, event_id: str) -> dict:
        token = await self._get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            return {"deleted": resp.status_code == 204}

    async def test_connection(self, config: dict) -> dict:
        try:
            if isinstance(config.get("credentials"), str):
                self._creds = json.loads(config["credentials"])
            elif isinstance(config.get("credentials"), dict):
                self._creds = config["credentials"]
            token = await self._get_access_token()
            if token:
                return {"ok": True}
            return {"ok": False, "error": "Could not get access token"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_setup_instructions(self) -> dict:
        return {
            "platform": "calendar",
            "steps": [
                "1. Enable Google Calendar API in Cloud Console",
                "2. Create OAuth2 credentials (Web application type)",
                "3. Get refresh token via OAuth2 flow",
                "4. Provide JSON with client_id, client_secret, refresh_token",
            ],
            "required_fields": ["credentials"],
        }


# Registry of all adapters
ADAPTERS: dict[str, type[PlatformAdapter]] = {
    "telegram": TelegramAdapter,
    "whatsapp": WhatsAppAdapter,
    "discord": DiscordAdapter,
    "slack": SlackAdapter,
    "gmail": GmailAdapter,
    "spotify": SpotifyAdapter,
    "calendar": CalendarAdapter,
}


def get_adapter(platform: str, config: dict = None) -> PlatformAdapter:
    """Create adapter instance with config."""
    cls = ADAPTERS.get(platform)
    if not cls:
        raise ValueError(f"Unknown platform: {platform}")
    if config:
        return cls(**config)
    return cls()
