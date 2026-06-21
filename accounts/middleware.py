from django.contrib.auth.models import AnonymousUser
from django.shortcuts import redirect


PUBLIC_PREFIXES = (
    '/accounts/login/',
    '/accounts/register/',
    '/admin/',
    '/sharing/public/',
    '/static/',
)


class PhoneAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if isinstance(request.user, AnonymousUser):
            if not any(request.path.startswith(p) for p in PUBLIC_PREFIXES):
                return redirect('accounts:login')
        return self.get_response(request)
