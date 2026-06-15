from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from crm.models import User, Dialog, Message, Fan, Model as PersonaModel
from crm.api.frontend.restful.serializers.serializers import DialogListSerializer, MessageSerializer, UserSerializer
from crm.services import get_online_users, calculate_overdue_dialogs_count
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class ChatterPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'chatter'

class TeamleadPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'teamlead'

from rest_framework.pagination import CursorPagination

class DialogPagination(CursorPagination):
    ordering = '-last_message_at'

class DialogViewSet(mixins.DestroyModelMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = DialogListSerializer
    permission_classes = [ChatterPermission]
    pagination_class = DialogPagination

    def get_queryset(self):
        return Dialog.objects.filter(chatter=self.request.user)

@api_view(['GET'])
@permission_classes([ChatterPermission])
def dialog_messages(request, pk):
    dialog = get_object_or_404(Dialog, pk=pk, chatter=request.user)
    messages = dialog.messages.all().order_by('-created_at')
    
    from rest_framework.pagination import CursorPagination
    paginator = CursorPagination()
    paginator.ordering = '-created_at'
    
    page = paginator.paginate_queryset(messages, request)
    serializer = MessageSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)

@api_view(['POST'])
@permission_classes([ChatterPermission])
def mark_dialog_read(request, pk):
    dialog = get_object_or_404(Dialog, pk=pk, chatter=request.user)
    dialog.unread_count = 0
    dialog.save(update_fields=['unread_count'])
    return Response({'status': 'ok'})

@api_view(['GET'])
@permission_classes([TeamleadPermission])
def teamlead_overview(request):
    chatters = User.objects.filter(role='chatter')
    chatter_ids = [c.id for c in chatters]
    online_status = get_online_users(chatter_ids)
    
    from django.conf import settings
    
    data = []
    for c in chatters:
        if not online_status.get(c.id, False):
            continue
            
        dialogs = Dialog.objects.filter(chatter=c)
        active_count = dialogs.count()
        overdue_count = 0
        waiting_count = 0
        max_silence_start = None
        
        for d in dialogs:
            last_msg = d.messages.order_by('-created_at').first()
            if last_msg and last_msg.sender_type == 'fan':
                waiting_count += 1
                delta = timezone.now() - last_msg.created_at
                if delta.total_seconds() > (settings.OVERDUE_THRESHOLD_MINUTES * 60):
                    overdue_count += 1
                if not max_silence_start or last_msg.created_at < max_silence_start:
                    max_silence_start = last_msg.created_at
        
        data.append({
            'chatter_id': c.id,
            'chatter_name': c.username,
            'active_dialogs': active_count,
            'waiting_dialogs': waiting_count,
            'overdue_dialogs': overdue_count,
            'max_silence_start': max_silence_start.isoformat() if max_silence_start else None
        })
    return Response(data)

@api_view(['POST'])
def emulate_incoming(request):
    dialog_id = request.data.get('dialog_id')
    chatter_id = request.data.get('chatter_id')
    force_new = request.data.get('force_new', False)
    text = request.data.get('text', 'Hello, this is a simulated message.')
    
    if not dialog_id or force_new:
        if chatter_id:
            chatter = get_object_or_404(User, pk=chatter_id, role='chatter')
        else:
            chatter = User.objects.filter(role='chatter').first()
            
        if not chatter:
            return Response({'error': 'No chatters available'}, status=status.HTTP_400_BAD_REQUEST)
            
        persona, _ = PersonaModel.objects.get_or_create(name='Simulated Model')
        
        if force_new:
            import uuid
            fan_id = f'sim_fan_{uuid.uuid4().hex[:8]}'
            fan = Fan.objects.create(internal_id=fan_id, name=f'New Fan {fan_id[-4:]}')
            dialog = Dialog.objects.create(model=persona, fan=fan, chatter=chatter)
        else:
            fan, _ = Fan.objects.get_or_create(internal_id='sim_fan_1', defaults={'name': 'Simulated Fan'})
            dialog, _ = Dialog.objects.get_or_create(model=persona, fan=fan, defaults={'chatter': chatter})
        
        dialog_id = dialog.id
    else:
        dialog = get_object_or_404(Dialog, pk=dialog_id)

    with transaction.atomic():
        msg = Message.objects.create(
            dialog=dialog,
            sender_type='fan',
            text=text,
        )
        dialog.last_message_at = timezone.now()
        dialog.unread_count += 1
        dialog.save(update_fields=['last_message_at', 'unread_count'])
    
    # Broadcast new message event
    channel_layer = get_channel_layer()
    event_data = {
        'type': 'chat_message',
        'message': MessageSerializer(msg).data,
        'dialog_id': dialog.id,
        'unread_count': dialog.unread_count,
    }
    async_to_sync(channel_layer.group_send)(f'dialog_{dialog.id}', event_data)
    
    if dialog.chatter:
        async_to_sync(channel_layer.group_send)(f'chatter_{dialog.chatter.id}', event_data)

    return Response({'status': 'ok', 'message_id': msg.id, 'dialog_id': dialog.id})
