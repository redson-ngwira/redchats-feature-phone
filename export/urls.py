from django.urls import path
from . import views

app_name = 'export'

urlpatterns = [
    path('<int:pk>/', views.export_sms, name='export_sms'),
]
