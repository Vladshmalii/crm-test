import uuid

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db import transaction
from django.db.models import F, Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response

from crm.choices import SenderType, UserRole
from crm.models import Dialog, Fan, Message, Persona, User
from crm.api.frontend.restful.serializers.serializers import (
    DialogListSerializer,
    MessageSerializer,
)
from crm.services import overdue_service, presence_service


class RolePermission(permissions.BasePermission):
    required_role = None

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == self.required_role
        )


class IsChatter(RolePermission):
    required_role = UserRole.CHATTER


class IsTeamlead(RolePermission):
    required_role = UserRole.TEAMLEAD


class DialogPagination(CursorPagination):
    ordering = '-last_message_at'


class DialogViewSet(mixins.DestroyModelMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = DialogListSerializer
    permission_classes = [IsChatter]
    pagination_class = DialogPagination

    def get_queryset(self):
        return (
            Dialog.objects
            .filter(chatter=self.request.user)
            .select_related('persona', 'fan')
            .prefetch_related(
                Prefetch(
                    'messages',
                    queryset=Message.objects.order_by('-created_at')[:1],
                    to_attr='_prefetched_messages',
                ),
            )
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        return context

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return response


@api_view(['GET'])
@permission_classes([IsChatter])
def dialog_messages(request, pk):
    dialog = get_object_or_404(Dialog, pk=pk, chatter=request.user)
    messages_qs = dialog.messages.all().order_by('-created_at')

    paginator = CursorPagination()
    paginator.ordering = '-created_at'

    page = paginator.paginate_queryset(messages_qs, request)
    serializer = MessageSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['POST'])
@permission_classes([IsChatter])
def mark_dialog_read(request, pk):
    dialog = get_object_or_404(Dialog, pk=pk, chatter=request.user)
    dialog.unread_count = 0
    dialog.save(update_fields=['unread_count'])
    return Response({'status': 'ok'})


@api_view(['GET'])
@permission_classes([IsTeamlead])
def teamlead_overview(request):
    chatters = User.objects.filter(role=UserRole.CHATTER)
    chatter_ids = list(chatters.values_list('id', flat=True))
    online_status = presence_service.get_online_statuses(chatter_ids)

    online_chatters = [c for c in chatters if online_status.get(c.id, False)]

    data = []
    for chatter in online_chatters:
        dialogs_qs = Dialog.objects.filter(chatter=chatter)
        dialogs_qs = overdue_service.annotate_dialogs_with_last_fan_message(dialogs_qs)

        active_count = dialogs_qs.count()
        waiting_count = 0
        overdue_count = 0
        max_silence_start = None

        for d in dialogs_qs:
            if not d.last_fan_message_at:
                continue

            waiting_count += 1

            if overdue_service.is_dialog_overdue(d.last_fan_message_at):
                overdue_count += 1

            if not max_silence_start or d.last_fan_message_at < max_silence_start:
                max_silence_start = d.last_fan_message_at

        data.append({
            'chatter_id': chatter.id,
            'chatter_name': chatter.username,
            'active_dialogs': active_count,
            'waiting_dialogs': waiting_count,
            'overdue_dialogs': overdue_count,
            'max_silence_start': max_silence_start.isoformat() if max_silence_start else None,
        })

    return Response(data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def emulate_incoming(request):
    dialog_id = request.data.get('dialog_id')
    chatter_id = request.data.get('chatter_id')
    force_new = request.data.get('force_new', False)
    text = request.data.get('text', 'Hello, this is a simulated message.')

    if not dialog_id or force_new:
        if chatter_id:
            chatter = get_object_or_404(User, pk=chatter_id, role=UserRole.CHATTER)
        else:
            chatter = User.objects.filter(role=UserRole.CHATTER).first()

        if not chatter:
            return Response(
                {'error': 'No chatters available'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        persona, _ = Persona.objects.get_or_create(name='Simulated Model')

        if force_new:
            fan_id = f'sim_fan_{uuid.uuid4().hex[:8]}'
            fan = Fan.objects.create(internal_id=fan_id, name=f'New Fan {fan_id[-4:]}')
            dialog = Dialog.objects.create(persona=persona, fan=fan, chatter=chatter)
        else:
            fan, _ = Fan.objects.get_or_create(
                internal_id='sim_fan_1',
                defaults={'name': 'Simulated Fan'},
            )
            dialog, _ = Dialog.objects.get_or_create(
                persona=persona,
                fan=fan,
                defaults={'chatter': chatter},
            )

        dialog_id = dialog.id
    else:
        dialog = get_object_or_404(Dialog, pk=dialog_id)

    with transaction.atomic():
        msg = Message.objects.create(
            dialog=dialog,
            sender_type=SenderType.FAN,
            text=text,
        )
        Dialog.objects.filter(pk=dialog.pk).update(
            last_message_at=timezone.now(),
            unread_count=F('unread_count') + 1,
        )
        dialog.refresh_from_db()

    channel_layer = get_channel_layer()
    event_data = {
        'type': 'chat_message',
        'message': MessageSerializer(msg).data,
        'dialog_id': dialog.id,
        'unread_count': dialog.unread_count,
    }
    async_to_sync(channel_layer.group_send)(f'dialog_{dialog.id}', event_data)

    if dialog.chatter_id:
        async_to_sync(channel_layer.group_send)(
            f'chatter_{dialog.chatter_id}',
            event_data,
        )

    return Response({
        'status': 'ok',
        'message_id': msg.id,
        'dialog_id': dialog.id,
    })
