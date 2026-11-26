"""
Production-grade Django Channels WebSocket consumers for Rojgar Setu.
Provides authenticated per-user real-time event streaming:
- Instant job application alerts & live applicant card injection
- Live agreement execution notifications
- Real-time chat notifications
"""

import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


@database_sync_to_async
def _get_session_user_id(session):
    """Safely reads rojgar_user_id from Django's DB-backed session in async context."""
    if not session:
        return None
    return session.get("rojgar_user_id")


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Authenticated WebSocket consumer bound to the user's session ID.
    Joins group `user_<user_id>` to receive real-time events.
    """

    async def connect(self):
        user_id = await _get_session_user_id(self.scope.get("session"))

        if not user_id:
            await self.close(code=4001)
            return

        self.user_id = str(user_id)
        self.group_name = f"user_{self.user_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "user_id": self.user_id,
        }))

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """Handle lightweight client keep-alive pings."""
        if not text_data:
            return
        try:
            data = json.loads(text_data)
            if data.get("type") == "ping":
                await self.send(text_data=json.dumps({"type": "pong"}))
        except Exception:
            pass

    async def broadcast_event(self, event):
        """Forwards server-pushed events to the connected WebSocket client."""
        await self.send(text_data=json.dumps({
            "type": event["event_type"],
            "payload": event["payload"],
        }))
