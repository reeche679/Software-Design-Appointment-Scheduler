from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse, resolve

class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get the current URL path
        path = request.path
        
        # If it's the root path and user is not authenticated, redirect to login
        if path == '/' and not request.user.is_authenticated:
            return redirect('login')
            
        # Allow access to login and register pages
        if path.startswith('/accounts/'):
            return self.get_response(request)
            
        # Redirect to login if not authenticated
        if not request.user.is_authenticated:
            return redirect('login')
            
        return self.get_response(request) 