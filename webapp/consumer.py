from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer, AsyncJsonWebsocketConsumer
from channels.layers import get_channel_layer
from webapp.models import Feedback, Reservation


class NotificationClient(AsyncJsonWebsocketConsumer):

    @database_sync_to_async
    def get_data(self):
        feedbacks_request = Feedback.objects.filter(status='N').count()
        return {
                "feedbacks_request": feedbacks_request,
        }

    async def connect(self):
        await self.channel_layer.group_add(
            "notification_group",
            self.channel_name,
        )
        await self.accept()
        channel_layer = get_channel_layer()
        await channel_layer.group_send("notification_group", {
            "type": "notify",
            "content": await self.get_data()
        })

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("notification_group",
                                               self.channel_name)

    async def notify(self, event):
        await self.send_json(event["content"])


class ReservationNotificationClient(AsyncJsonWebsocketConsumer):

    async def connect(self):
        await self.channel_layer.group_add(
            "notification_group_2",
            self.channel_name,
        )
        await self.accept()
        channel_layer = get_channel_layer()
        await channel_layer.group_send("notification_group_2", {
            "type": "notify",
            "content": {
                "message": "Новая бронь"
            }
        })

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("notification_group_2",
                                               self.channel_name)

    async def notify(self, event):
        await self.send_json(event["content"])
