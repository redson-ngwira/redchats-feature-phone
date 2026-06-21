from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone


def get_usage(user):
    from chat.models import Message
    now = timezone.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    total = Message.objects.filter(
        conversation__user=user,
        created_at__gte=start_of_day,
        role='assistant',
    ).aggregate(total=Sum('token_count'))['total'] or 0
    return total


def add_usage(user, tokens):
    pass


def check_limit(user):
    usage = get_usage(user)
    limit = settings.CEREBRAS_DAILY_TOKEN_LIMIT
    threshold = settings.CEREBRAS_TOKEN_WARN_THRESHOLD
    percent = (usage / limit * 100) if limit > 0 else 0
    return {
        'usage': usage,
        'limit': limit,
        'percent': min(percent, 100),
        'warning': percent >= (threshold * 100),
    }
