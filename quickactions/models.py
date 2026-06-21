from django.db import models
from django.conf import settings


class QuickAction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quick_actions')
    key_number = models.IntegerField()
    label = models.CharField(max_length=30)
    prompt_template = models.CharField(max_length=200)

    class Meta:
        ordering = ['key_number']
        unique_together = ['user', 'key_number']

    def __str__(self):
        return f'{self.key_number}: {self.label}'
