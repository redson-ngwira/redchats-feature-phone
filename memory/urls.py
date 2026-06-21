from django.urls import path
from . import views

app_name = 'memory'

urlpatterns = [
    path('', views.memory_list, name='list'),
    path('new/', views.memory_create, name='create'),
    path('<int:pk>/edit/', views.memory_edit, name='edit'),
    path('<int:pk>/delete/', views.memory_delete, name='delete'),
    path('extract/<int:pk>/', views.memory_extract, name='extract'),
]
