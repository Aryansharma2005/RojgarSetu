"""WebSocket URL routing for Rojgar Setu."""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"^ws/notifications/$", consumers.NotificationConsumer.as_asgi()),
]
