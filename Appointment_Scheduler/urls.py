from django.contrib import admin
from django.urls import path
from django.contrib.auth.views import LogoutView
from AppointmentWebsite import views
from AppointmentWebsite.auth import user_login, user_logout, register
from django.shortcuts import redirect

"""
URL configuration for Appointment_Scheduler project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('login'), name='root'),
    path('home/', views.homepage, name='home'),
    path('accounts/login/', user_login, name='login'),
    path('accounts/logout/', user_logout, name='logout'),
    path('accounts/register/', register, name='register'),
    path('book-appointment/', views.book_appointment, name='book_appointment'),
]
