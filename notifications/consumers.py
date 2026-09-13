import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    One group per authenticated user: `notifications_<user_id>`.
    Anything sent server-side via `push_notification()` in tasks.py
    is broadcast to every open tab/socket for that user in real time
    (e.g. a fee-payment confirmation or a new grade alert).
    """

    async def connect(self):
        user = self.scope['user']
        if not user.is_authenticated:
            await self.close()
            return
        self.group_name = f'notifications_{user.id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # Clients don't need to send anything; this is a push-only channel.
        pass

    async def notify(self, event):
        await self.send_json({
            'message': event['message'],
            'notification_type': event.get('notification_type', 'announcement'),
        })
