from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('chat/', include('chat.urls')),
    path('conversations/', include('conversations.urls')),
    path('personas/', include('personas.urls')),
    path('quickactions/', include('quickactions.urls')),
    path('memory/', include('memory.urls')),
    path('sharing/', include('sharing.urls')),
    path('export/', include('export.urls')),
    path('', RedirectView.as_view(url='/accounts/login/'), name='home'),
]
