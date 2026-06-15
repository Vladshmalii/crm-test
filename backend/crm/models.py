from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from crm.choices import ROLE_CHOICES, SENDER_CHOICES, STATUS_CHOICES

class User(AbstractUser):
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='chatter')

class Model(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Fan(models.Model):
    internal_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.internal_id})"

class Dialog(models.Model):
    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name='dialogs')
    fan = models.ForeignKey(Fan, on_delete=models.CASCADE, related_name='dialogs')
    chatter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_dialogs')
    
    last_message_at = models.DateTimeField(default=timezone.now)
    unread_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ('model', 'fan')

    def __str__(self):
        return f"Dialog: {self.model.name} & {self.fan.name}"

class Message(models.Model):
    dialog = models.ForeignKey(Dialog, on_delete=models.CASCADE, related_name='messages')
    sender_type = models.CharField(max_length=20, choices=SENDER_CHOICES)
    text = models.TextField()
    
    is_ppv = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Msg {self.id} in {self.dialog}"
