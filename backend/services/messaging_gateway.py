"""Messaging gateway — normalize inbound messages, route through agentic loop, send responses."""
import json
import logging
import uuid
from typing import Optional

from services.platform_adapters import NormalizedMessage, get_adapter

logger = logging.getLogger(__name__)


class MessagingGateway:
    """Route external platform messages through the unified agentic loop."""

    async def handle_inbound(self, platform: str, payload: dict, adapter_config: dict) -> dict:
        """
        Process inbound message from any platform.
        1. Parse with adapter
        2. Find/create conversation
        3. Run through agentic loop (non-streaming)
        4. Send response back via adapter
        5. Log everything
        """
        from services.memory_service import memory_service
        from services.agentic_loop import agentic_loop

        # Parse message
        adapter = get_adapter(platform, adapter_config)
        msg = adapter.parse_inbound(payload)
        if not msg:
            return {"handled": False, "reason": "Could not parse message"}

        if not msg.text.strip():
            return {"handled": False, "reason": "Empty message"}

        # Find or create conversation keyed by platform + chat_id
        conversation_id = self._find_conversation(platform, msg.chat_id)
        if not conversation_id:
            conversation_id = memory_service.create_conversation(
                mode="messaging", source=platform
            )
            self._store_conversation_mapping(platform, msg.chat_id, conversation_id)

        # Log inbound
        self._log_integration_message(
            platform, conversation_id, "inbound", msg.text, msg.platform_message_id
        )

        # Build messages list from recent history
        history = memory_service.get_conversation_messages(conversation_id, limit=20)
        messages = []
        for h in history:
            author = "user" if h["author"] == "user" else "model"
            messages.append({
                "author": h["author"],
                "parts": [{"text": h["content"]}],
            })
        # Add current message
        messages.append({
            "author": "user",
            "parts": [{"text": msg.text}],
        })

        # Run through agentic loop (collect full response, non-streaming)
        response_text = ""
        async for chunk in agentic_loop.run(
            messages=messages,
            conversation_id=conversation_id,
            mode="messaging",
            provider="gemini",  # Default for messaging
            source_platform=platform,
            inject_skills=True,
        ):
            if chunk.get("type") == "token":
                response_text += chunk.get("content", "")

        if not response_text:
            response_text = "I couldn't generate a response. Please try again."

        # Send response back
        try:
            send_result = await adapter.send_response(msg.chat_id, response_text)
        except Exception as e:
            logger.error(f"Failed to send response to {platform}: {e}")
            send_result = {"error": str(e)}

        # Log outbound
        self._log_integration_message(
            platform, conversation_id, "outbound", response_text
        )

        return {
            "handled": True,
            "platform": platform,
            "conversation_id": conversation_id,
            "response_length": len(response_text),
            "send_result": send_result,
        }

    def _find_conversation(self, platform: str, chat_id: str) -> Optional[str]:
        """Find existing conversation for this platform + chat_id."""
        from services.memory_service import memory_service
        conn = memory_service._get_conn()
        try:
            # Look up via integration_messages
            row = conn.execute(
                "SELECT conversation_id FROM integration_messages "
                "WHERE metadata LIKE ? ORDER BY created_at DESC LIMIT 1",
                (f'%"chat_id":"{chat_id}"%',),
            ).fetchone()
            if row:
                return row[0]
        except Exception:
            pass
        return None

    def _store_conversation_mapping(self, platform: str, chat_id: str, conversation_id: str):
        """Store initial mapping from platform chat to conversation."""
        self._log_integration_message(
            platform, conversation_id, "system",
            f"Conversation started from {platform}",
            metadata={"chat_id": chat_id}
        )

    def _log_integration_message(
        self,
        platform: str,
        conversation_id: str,
        direction: str,
        content: str,
        platform_message_id: str = "",
        metadata: dict = None,
    ):
        from services.memory_service import memory_service
        conn = memory_service._get_conn()
        msg_id = str(uuid.uuid4())
        # Find integration_id
        integration_id = ""
        try:
            row = conn.execute(
                "SELECT id FROM integrations WHERE platform = ?", (platform,)
            ).fetchone()
            if row:
                integration_id = row[0]
        except Exception:
            pass

        conn.execute(
            "INSERT INTO integration_messages "
            "(id, integration_id, conversation_id, direction, platform_message_id, content, metadata) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (msg_id, integration_id, conversation_id, direction, platform_message_id,
             content, json.dumps(metadata or {})),
        )
        conn.commit()


# Singleton
messaging_gateway = MessagingGateway()
