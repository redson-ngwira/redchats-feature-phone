from django.urls import path
from . import views

app_name = 'sharing'

urlpatterns = [
    path('', views.share_list, name='list'),
    path('new/', views.share_create, name='create'),
    path('import/', views.share_import, name='import'),
    path('public/<str:code>/', views.share_public, name='public'),
]
