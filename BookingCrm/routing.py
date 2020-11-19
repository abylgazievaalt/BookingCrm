from channels.routing import ProtocolTypeRouter
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

from webapp.consumer import NotificationClient, ReservationNotificationClient

websockets = URLRouter([
    path(
        "ws/notifications/",
        NotificationClient,
        name="ws_notifications",
    ),
    path(
        "ws/reservations/",
        ReservationNotificationClient,
        name="ws_reservations",
    ),
])

application = ProtocolTypeRouter({
    # Empty for now (http->django views is added by default)
    "websocket": AuthMiddlewareStack(websockets),
})
