from django.urls import path
from . import views

app_name = 'conversations'

urlpatterns = [
    path('', views.conversation_list, name='list'),
    path('new/', views.conversation_create, name='create'),
    path('<int:pk>/rename/', views.conversation_rename, name='rename'),
    path('<int:pk>/delete/', views.conversation_delete, name='delete'),
    path('<int:pk>/pin/', views.conversation_pin, name='pin'),
]
