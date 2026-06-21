from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_view, name='chat'),
    path('chunk/<str:direction>/', views.chunk_nav, name='chunk_nav'),
    path('model/', views.model_select, name='model_select'),
]
