import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db import close_old_connections

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        close_old_connections()  # fecha conexões antigas herdadas
        self.device_mac = self.scope['url_route']['kwargs']['device_mac']
        self.group_name = f'dashboard_{self.device_mac}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        close_old_connections()

    async def device_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'device_update',
            'updated_now': event['updated_now'],
            'updated_at': event['updated_at']
        }))

    async def sensor_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'sensor_update',
            'sensor_type': event['sensor_type'],
            'value': event['value']
        }))
