from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse, resolve

class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Pre-compile exempt paths
        self.exempt_paths = ['/accounts/login/', '/accounts/register/']

    def __call__(self, request):
        path = request.path.rstrip('/')
        
        # Always allow access to login, register, and static files
        if path in self.exempt_paths or path.startswith('/static/') or path.startswith('/accounts/'):
            return self.get_response(request)
            
        # Handle other paths
        if not request.user.is_authenticated:
            return redirect('login')
            
        return self.get_response(request)