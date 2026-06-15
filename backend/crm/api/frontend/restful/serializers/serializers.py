from rest_framework import serializers
from crm.models import User, Dialog, Message, Model, Fan

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'role']

class ModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Model
        fields = ['id', 'name']

class FanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fan
        fields = ['id', 'internal_id', 'name']

class DialogListSerializer(serializers.ModelSerializer):
    model = ModelSerializer()
    fan = FanSerializer()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Dialog
        fields = ['id', 'model', 'fan', 'last_message_at', 'unread_count', 'last_message']

    def get_last_message(self, obj):
        msg = obj.messages.order_by('-created_at').first()
        if msg:
            return {
                'text': msg.text,
                'sender_type': msg.sender_type
            }
        return None

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'sender_type', 'text', 'is_ppv', 'price', 'created_at', 'status']
