from django.db import models
from django.conf import settings


class MemoryItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memories')
    key = models.CharField(max_length=100)
    value = models.TextField()
    source_conversation = models.ForeignKey(
        'conversations.Conversation', on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.key}: {self.value[:50]}'
