"""
Fault-tolerant real-time WebSocket broadcast helper for Rojgar Setu.
Used by synchronous Django views to push instant events over Channels.
"""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_user_event(user_id, event_type: str, payload: dict) -> None:
    """
    Sends a typed real-time event to all active WebSocket connections of `user_id`.
    Gracefully no-ops if channel layer is unavailable.
    """
    if not user_id:
        return
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        group_name = f"user_{str(user_id)}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "broadcast_event",
                "event_type": event_type,
                "payload": payload,
            },
        )
    except Exception as exc:
        print(f"[Realtime WS] Broadcast error ({event_type}): {exc}")
