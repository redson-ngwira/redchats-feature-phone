from django.contrib import admin
from .models import Message, SavedResponse

admin.site.register(Message)
admin.site.register(SavedResponse)
