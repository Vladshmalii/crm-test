from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from crm.choices import MessageStatus, SenderType, UserRole


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CHATTER,
        db_index=True,
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_chatter(self) -> bool:
        return self.role == UserRole.CHATTER

    @property
    def is_teamlead(self) -> bool:
        return self.role == UserRole.TEAMLEAD


class Persona(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Persona'
        verbose_name_plural = 'Personas'
        db_table = 'crm_model'

    def __str__(self):
        return self.name


class Fan(models.Model):
    internal_id = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Fan'
        verbose_name_plural = 'Fans'

    def __str__(self):
        return f"{self.name} ({self.internal_id})"


class Dialog(models.Model):
    persona = models.ForeignKey(
        Persona,
        on_delete=models.CASCADE,
        related_name='dialogs',
    )
    fan = models.ForeignKey(
        Fan,
        on_delete=models.CASCADE,
        related_name='dialogs',
    )
    chatter = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_dialogs',
        db_index=True,
    )

    last_message_at = models.DateTimeField(default=timezone.now)
    unread_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Dialog'
        verbose_name_plural = 'Dialogs'
        constraints = [
            models.UniqueConstraint(
                fields=['persona', 'fan'],
                name='unique_persona_fan_dialog',
            ),
        ]
        ordering = ['-last_message_at']

    def __str__(self):
        return f"Dialog: {self.persona.name} & {self.fan.name}"


class Message(models.Model):
    dialog = models.ForeignKey(
        Dialog,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender_type = models.CharField(
        max_length=20,
        choices=SenderType.choices,
        db_index=True,
    )
    text = models.TextField()

    is_ppv = models.BooleanField(default=False)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=MessageStatus.choices,
        default=MessageStatus.SENT,
    )

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    def __str__(self):
        return f"Msg {self.id} in {self.dialog}"
