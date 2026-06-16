from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Dialog, Fan, Message, Persona, User


class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Role Info', {'fields': ('role',)}),
    )
    list_display = ('id', 'username', 'role', 'is_active')
    list_filter = ('role', 'is_active')


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Fan)
class FanAdmin(admin.ModelAdmin):
    list_display = ('id', 'internal_id', 'name')
    search_fields = ('name', 'internal_id')


@admin.register(Dialog)
class DialogAdmin(admin.ModelAdmin):
    list_display = ('id', 'persona', 'fan', 'chatter', 'last_message_at', 'unread_count')
    list_filter = ('persona', 'chatter')
    raw_id_fields = ('persona', 'fan', 'chatter')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'dialog', 'sender_type', 'is_ppv', 'status', 'created_at')
    list_filter = ('sender_type', 'is_ppv', 'status')
    raw_id_fields = ('dialog',)


admin.site.register(User, CustomUserAdmin)
