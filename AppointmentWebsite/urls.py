from django.contrib import admin
from django.urls import path
from AppointmentWebsite import views
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('book-appointment/', views.book_appointment, name='book_appointment'),
]
