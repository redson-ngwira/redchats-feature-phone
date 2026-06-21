from django.contrib.auth.models import AnonymousUser


class PhoneAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if isinstance(request.user, AnonymousUser):
            public_prefixes = ('/accounts/login/', '/accounts/register/', '/admin/', '/sharing/public/')
            if not any(request.path.startswith(p) for p in public_prefixes):
                return __import__('django.shortcuts', fromlist=['redirect']).redirect('accounts:login')
        return self.get_response(request)
