from django.db import models


class UserRole(models.TextChoices):
    CHATTER = 'chatter', 'Chatter'
    TEAMLEAD = 'teamlead', 'Teamlead'


class SenderType(models.TextChoices):
    FAN = 'fan', 'Fan'
    CHATTER = 'chatter', 'Chatter'


class MessageStatus(models.TextChoices):
    SENT = 'sent', 'Sent'
    READ = 'read', 'Read'
