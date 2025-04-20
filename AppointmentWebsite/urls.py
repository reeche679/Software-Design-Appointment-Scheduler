from django.urls import path
from AppointmentWebsite import views
from AppointmentWebsite import auth
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('book-appointment/', views.book_appointment, name='book_appointment'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('download-file/<int:file_id>/', views.download_file, name='download_file'),
    path('messages/', views.messages_view, name='messages'),
    path('send_message/', views.send_message, name='send_message'),
]
