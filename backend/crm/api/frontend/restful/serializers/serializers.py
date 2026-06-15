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
    
    class Meta:
        model = Dialog
        fields = ['id', 'model', 'fan', 'last_message_at', 'unread_count']

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'sender_type', 'text', 'is_ppv', 'price', 'created_at', 'status']
