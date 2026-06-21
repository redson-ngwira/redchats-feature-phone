from django.db import models
from django.conf import settings


class Persona(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='personas')
    name = models.CharField(max_length=50)
    system_prompt = models.TextField()
    is_default = models.BooleanField(default=False)
    is_shared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
