from django.urls import path
from . import views

app_name = 'personas'

urlpatterns = [
    path('', views.persona_list, name='list'),
    path('new/', views.persona_create, name='create'),
    path('<int:pk>/edit/', views.persona_edit, name='edit'),
    path('<int:pk>/delete/', views.persona_delete, name='delete'),
]
