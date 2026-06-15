from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Model, Fan, Dialog, Message

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Role Info', {'fields': ('role',)}),
    )

@admin.register(Model)
class ModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

@admin.register(Fan)
class FanAdmin(admin.ModelAdmin):
    list_display = ('id', 'internal_id', 'name')

@admin.register(Dialog)
class DialogAdmin(admin.ModelAdmin):
    list_display = ('id', 'model', 'fan', 'chatter', 'last_message_at', 'unread_count')
    list_filter = ('model', 'chatter')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'dialog', 'sender_type', 'is_ppv', 'status', 'created_at')
    list_filter = ('sender_type', 'is_ppv', 'status')

admin.site.register(User, CustomUserAdmin)
