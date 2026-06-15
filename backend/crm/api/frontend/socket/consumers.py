import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from crm.models import User, Dialog

@database_sync_to_async
def get_user_from_token(token):
    try:
        access_token = AccessToken(token)
        user = User.objects.get(id=access_token['user_id'])
        return user
    except Exception:
        return AnonymousUser()

import asyncio

class CrmConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope['query_string'].decode()
        token = None
        if 'token=' in query_string:
            token = query_string.split('token=')[1].split('&')[0]
        
        self.user = await get_user_from_token(token)
        
        if self.user.is_anonymous:
            await self.close()
            return
            
        await self.accept()

        if self.user.role == 'teamlead':
            await self.channel_layer.group_add('teamlead', self.channel_name)
        elif self.user.role == 'chatter':
            await self.channel_layer.group_add(f'chatter_{self.user.id}', self.channel_name)
            
            # Add to dialog groups
            dialogs = await self.get_chatter_dialogs(self.user.id)
            for dialog_id in dialogs:
                await self.channel_layer.group_add(f'dialog_{dialog_id}', self.channel_name)
                
            # Start presence loop
            self.presence_task = asyncio.create_task(self.presence_loop())

    async def disconnect(self, close_code):
        if not hasattr(self, 'user') or self.user.is_anonymous:
            return
            
        if hasattr(self, 'presence_task'):
            self.presence_task.cancel()
            await self.remove_presence()
            
        if self.user.role == 'teamlead':
            await self.channel_layer.group_discard('teamlead', self.channel_name)
        elif self.user.role == 'chatter':
            await self.channel_layer.group_discard(f'chatter_{self.user.id}', self.channel_name)
            dialogs = await self.get_chatter_dialogs(self.user.id)
            for dialog_id in dialogs:
                await self.channel_layer.group_discard(f'dialog_{dialog_id}', self.channel_name)

    async def presence_loop(self):
        try:
            while True:
                await self.update_presence()
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            pass

    @database_sync_to_async
    def update_presence(self):
        from crm.services import set_user_online
        set_user_online(self.user.id)
        
    @database_sync_to_async
    def remove_presence(self):
        import os
        import redis
        redis_client = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
        redis_client.delete(f"presence_user_{self.user.id}")

    async def receive(self, text_data):
        # Handle message read or send
        data = json.loads(text_data)
        action = data.get('action')
        
        if action == 'send_message':
            dialog_id = data.get('dialog_id')
            text = data.get('text')
            is_ppv = data.get('is_ppv', False)
            price = data.get('price', None)
            
            msg = await self.save_message(dialog_id, text, is_ppv, price)
            
            # Broadcast to dialog group
            event_data = {
                'type': 'chat_message',
                'message': msg,
                'dialog_id': dialog_id,
            }
            await self.channel_layer.group_send(f'dialog_{dialog_id}', event_data)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def get_chatter_dialogs(self, user_id):
        return list(Dialog.objects.filter(chatter_id=user_id).values_list('id', flat=True))

    @database_sync_to_async
    def save_message(self, dialog_id, text, is_ppv, price):
        from crm.models import Message
        from django.utils import timezone
        dialog = Dialog.objects.get(id=dialog_id)
        msg = Message.objects.create(
            dialog=dialog,
            sender_type='chatter',
            text=text,
            is_ppv=is_ppv,
            price=price
        )
        dialog.last_message_at = timezone.now()
        dialog.save(update_fields=['last_message_at'])
        from crm.api.frontend.restful.serializers.serializers import MessageSerializer
        return MessageSerializer(msg).data
