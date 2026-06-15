import os
import redis
from django.conf import settings
from django.utils import timezone
from .models import Dialog

redis_client = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))

def set_user_online(user_id):
    key = f"presence_user_{user_id}"
    redis_client.setex(key, settings.PRESENCE_GRACE_SECONDS, 'online')

def is_user_online(user_id):
    return redis_client.exists(f"presence_user_{user_id}")

def get_online_users(user_ids):
    online_status = {}
    for uid in user_ids:
        online_status[uid] = is_user_online(uid)
    return online_status

def is_dialog_overdue(dialog):
    last_msg = dialog.messages.order_by('-created_at').first()
    if not last_msg or last_msg.sender_type == 'chatter':
        return False
    delta = timezone.now() - last_msg.created_at
    return delta.total_seconds() > (settings.OVERDUE_THRESHOLD_MINUTES * 60)

def calculate_overdue_dialogs_count(dialogs):
    count = 0
    for d in dialogs:
        if is_dialog_overdue(d):
            count += 1
    return count
