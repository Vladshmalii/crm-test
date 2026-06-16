import asyncio
import json
import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken

from crm.models import Dialog, Message, User
from crm.services import presence_service

logger = logging.getLogger(__name__)


@database_sync_to_async
def get_user_from_token(token):
    if not token:
        return AnonymousUser()
    try:
        access_token = AccessToken(token)
        return User.objects.get(id=access_token['user_id'])
    except (User.DoesNotExist, Exception) as e:
        logger.warning("WebSocket auth failed: %s", e)
        return AnonymousUser()


class CrmConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = AnonymousUser()
        self.presence_task = None

    async def connect(self):
        query_params = parse_qs(self.scope['query_string'].decode())
        token = query_params.get('token', [None])[0]

        self.user = await get_user_from_token(token)

        if self.user.is_anonymous:
            await self.close()
            return

        await self.accept()

        if self.user.is_teamlead:
            await self.channel_layer.group_add('teamlead', self.channel_name)
        elif self.user.is_chatter:
            await self.channel_layer.group_add(
                f'chatter_{self.user.id}',
                self.channel_name,
            )

            dialog_ids = await self._get_chatter_dialog_ids()
            for dialog_id in dialog_ids:
                await self.channel_layer.group_add(
                    f'dialog_{dialog_id}',
                    self.channel_name,
                )

            self.presence_task = asyncio.create_task(self._presence_loop())

    async def disconnect(self, close_code):
        if self.user.is_anonymous:
            return

        if self.presence_task:
            self.presence_task.cancel()
            await self._remove_presence()

        if self.user.is_teamlead:
            await self.channel_layer.group_discard('teamlead', self.channel_name)
        elif self.user.is_chatter:
            await self.channel_layer.group_discard(
                f'chatter_{self.user.id}',
                self.channel_name,
            )
            dialog_ids = await self._get_chatter_dialog_ids()
            for dialog_id in dialog_ids:
                await self.channel_layer.group_discard(
                    f'dialog_{dialog_id}',
                    self.channel_name,
                )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self._send_error('Invalid JSON')
            return

        action = data.get('action')

        if action == 'send_message':
            await self._handle_send_message(data)
        else:
            await self._send_error(f'Unknown action: {action}')

    async def _handle_send_message(self, data):
        dialog_id = data.get('dialog_id')
        text = data.get('text', '').strip()
        is_ppv = data.get('is_ppv', False)
        price = data.get('price')

        if not dialog_id or not text:
            await self._send_error('dialog_id and text are required')
            return

        msg = await self._save_message(dialog_id, text, is_ppv, price)
        if msg is None:
            await self._send_error('Dialog not found or access denied')
            return

        event_data = {
            'type': 'chat_message',
            'message': msg,
            'dialog_id': dialog_id,
        }
        await self.channel_layer.group_send(f'dialog_{dialog_id}', event_data)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def _send_error(self, message):
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message,
        }))

    async def _presence_loop(self):
        try:
            while True:
                await self._update_presence()
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            pass

    @database_sync_to_async
    def _update_presence(self):
        presence_service.set_online(self.user.id)

    @database_sync_to_async
    def _remove_presence(self):
        presence_service.set_offline(self.user.id)

    @database_sync_to_async
    def _get_chatter_dialog_ids(self):
        return list(
            Dialog.objects.filter(chatter_id=self.user.id)
            .values_list('id', flat=True)
        )

    @database_sync_to_async
    def _save_message(self, dialog_id, text, is_ppv, price):
        from django.utils import timezone
        from crm.api.frontend.restful.serializers.serializers import MessageSerializer

        try:
            dialog = Dialog.objects.get(id=dialog_id, chatter_id=self.user.id)
        except Dialog.DoesNotExist:
            return None

        msg = Message.objects.create(
            dialog=dialog,
            sender_type='chatter',
            text=text,
            is_ppv=is_ppv,
            price=price,
        )
        dialog.last_message_at = timezone.now()
        dialog.save(update_fields=['last_message_at'])
        return MessageSerializer(msg).data
