from django.contrib import admin
from django.urls import path
from AppointmentWebsite import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.homepage, name='home'),
    path('AppointmentForm/', views.book_appointment, name='book_appointment'),
    
]
