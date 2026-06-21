from django.urls import path
from . import views

app_name = 'quickactions'

urlpatterns = [
    path('', views.quickaction_list, name='list'),
    path('<int:pk>/edit/', views.quickaction_edit, name='edit'),
]
