import string
import random

from django.db import models
from django.conf import settings


def generate_share_code():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=6))


class SharedPrompt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shared_prompts')
    title = models.CharField(max_length=100)
    content = models.TextField()
    share_code = models.CharField(max_length=6, unique=True, default=generate_share_code)
    share_type = models.CharField(max_length=10, choices=[('persona', 'Persona'), ('prompt', 'Prompt')], default='prompt')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.title} ({self.share_code})'
