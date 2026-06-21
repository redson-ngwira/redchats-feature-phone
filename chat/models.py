from django.db import models
from django.conf import settings


class Message(models.Model):
    ROLE_CHOICES = [
        ('user', 'You'),
        ('assistant', 'AI'),
        ('system', 'System'),
    ]

    conversation = models.ForeignKey(
        'conversations.Conversation',
        on_delete=models.CASCADE,
        related_name='messages',
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    model_used = models.CharField(max_length=50, blank=True)
    token_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.role}: {self.content[:50]}'


class SavedResponse(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_responses')
    question = models.TextField(blank=True)
    response = models.TextField()
    conversation = models.ForeignKey(
        'conversations.Conversation', on_delete=models.SET_NULL, null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.response[:50]
