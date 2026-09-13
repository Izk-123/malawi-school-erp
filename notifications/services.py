"""Thin helper that fans a message out over Channels + persists it."""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Notification


def push_notification(user, message, notification_type=Notification.NotificationType.ANNOUNCEMENT):
    """Persist a Notification row and push it live over WebSocket if the
    user has an open connection. Safe to call even with the in-memory
    channel layer (single dev process) or with Redis in production."""
    Notification.objects.create(recipient=user, message=message, notification_type=notification_type)

    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        f'notifications_{user.id}',
        {'type': 'notify', 'message': message, 'notification_type': notification_type},
    )
