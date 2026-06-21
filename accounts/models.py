from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password, check_password


class UserProfile(AbstractUser):
    phone = models.CharField(max_length=20, unique=True)
    pin_hash = models.CharField(max_length=256)
    display_name = models.CharField(max_length=50, blank=True)
    default_model = models.CharField(max_length=50, default='gpt-oss-120b')

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    def set_pin(self, raw_pin):
        self.pin_hash = make_password(raw_pin)

    def check_pin(self, raw_pin):
        return check_password(raw_pin, self.pin_hash)

    def __str__(self):
        return self.display_name or self.phone
