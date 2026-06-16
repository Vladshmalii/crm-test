import os
from typing import Dict, List

import redis
from django.conf import settings
from django.db.models import Max, OuterRef, QuerySet, Subquery
from django.utils import timezone

from crm.choices import SenderType


def get_redis_client():
    return redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))


class PresenceService:
    PRESENCE_KEY_PREFIX = 'presence_user_'

    def __init__(self, redis_client=None):
        self._redis = redis_client or get_redis_client()

    def set_online(self, user_id: int) -> None:
        key = f"{self.PRESENCE_KEY_PREFIX}{user_id}"
        self._redis.setex(key, settings.PRESENCE_GRACE_SECONDS, 'online')

    def set_offline(self, user_id: int) -> None:
        self._redis.delete(f"{self.PRESENCE_KEY_PREFIX}{user_id}")

    def is_online(self, user_id: int) -> bool:
        return bool(self._redis.exists(f"{self.PRESENCE_KEY_PREFIX}{user_id}"))

    def get_online_statuses(self, user_ids: List[int]) -> Dict[int, bool]:
        if not user_ids:
            return {}

        pipe = self._redis.pipeline(transaction=False)
        for uid in user_ids:
            pipe.exists(f"{self.PRESENCE_KEY_PREFIX}{uid}")
        results = pipe.execute()

        return {uid: bool(status) for uid, status in zip(user_ids, results)}


class OverdueService:
    def __init__(self, threshold_minutes: int = None):
        self._threshold_minutes = threshold_minutes or settings.OVERDUE_THRESHOLD_MINUTES

    @property
    def threshold_seconds(self) -> int:
        return self._threshold_minutes * 60

    def get_overdue_cutoff(self):
        return timezone.now() - timezone.timedelta(seconds=self.threshold_seconds)

    def annotate_dialogs_with_last_fan_message(self, dialogs_qs: QuerySet) -> QuerySet:
        from crm.models import Message

        last_fan_msg_subquery = Message.objects.filter(
            dialog=OuterRef('pk'),
            sender_type=SenderType.FAN,
        ).order_by('-created_at').values('created_at')[:1]

        return dialogs_qs.annotate(
            last_fan_message_at=Subquery(last_fan_msg_subquery),
        )

    def is_dialog_overdue(self, last_fan_message_at) -> bool:
        if not last_fan_message_at:
            return False
        delta = timezone.now() - last_fan_message_at
        return delta.total_seconds() > self.threshold_seconds


presence_service = PresenceService()
overdue_service = OverdueService()
