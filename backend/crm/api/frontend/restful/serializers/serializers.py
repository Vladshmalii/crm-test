from rest_framework import serializers

from crm.models import Dialog, Fan, Message, Persona, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'role']


class PersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = ['id', 'name']


class FanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fan
        fields = ['id', 'internal_id', 'name']


class DialogListSerializer(serializers.ModelSerializer):
    persona = PersonaSerializer(read_only=True)
    fan = FanSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Dialog
        fields = ['id', 'persona', 'fan', 'last_message_at', 'unread_count', 'last_message']

    def get_last_message(self, obj):
        if hasattr(obj, '_prefetched_last_message'):
            msg = obj._prefetched_last_message
        else:
            msg = obj.messages.order_by('-created_at').first()

        if msg:
            return {
                'text': msg.text,
                'sender_type': msg.sender_type,
            }
        return None


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'sender_type', 'text', 'is_ppv', 'price', 'created_at', 'status']
