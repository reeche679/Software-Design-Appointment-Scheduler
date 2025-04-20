from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from Appointment_Scheduler import views  # Correct import for views
from AppointmentWebsite.auth import user_login, user_logout, register
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('login'), name='root'),
    path('home/', views.homepage, name='home'),
    path('accounts/login/', user_login, name='login'),
    path('accounts/logout/', user_logout, name='logout'),
    path('accounts/register/', register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),  # Correctly linked to the dashboard view
    path('book-appointment/', views.Book_Appointment, name='book_appointment'),
    path('profile/', views.profile, name='profile'),  # Added profile URL pattern
    path('profile/edit/', views.edit_profile, name='edit_profile'),  # Added edit_profile URL
    path('schedule/', views.schedule, name='schedule'),  # Added schedule URL pattern
    path('messages/', views.messages_view, name='messages'),  # Added messages URL pattern
    path('faculty-dashboard/', views.faculty_dashboard, name='faculty_dashboard'),  # Added faculty dashboard URL
    path('faculty-profile/', views.faculty_profile, name='faculty_profile'),  # Added faculty profile URL
    path('add-time-slot/', views.add_time_slot, name='add_time_slot'),  # Added time slot URL
    path('suggest-alternative/', views.suggest_alternative, name='suggest_alternative'),  # Added suggest alternative URL
    path('faculty-schedule/', views.faculty_schedule, name='faculty_schedule'),  # Added faculty schedule URL
    path('delete-time-slot/<int:slot_id>/', views.delete_time_slot, name='delete_time_slot'),  # Added delete time slot URL
    path('faculty-messages/', views.faculty_messages, name='faculty_messages'),
    path('mark-message-read/<int:message_id>/', views.mark_message_as_read, name='mark_message_as_read'),
    path('reply-to-message/<int:message_id>/', views.reply_to_message, name='reply_to_message'),
    path('confirm-appointment/', views.confirm_appointment, name='confirm_appointment'),
    path('send-message/', views.send_message, name='send_message'),
    path('appointment/<int:appointment_id>/approve/', views.approve_appointment, name='approve_appointment'),
    path('appointment/<int:appointment_id>/reject/', views.reject_appointment, name='reject_appointment'),
    
    # Include AppointmentWebsite URLs
    path('', include('AppointmentWebsite.urls')),
    
    # Password reset URLs
    path('password-reset/', 
         PasswordResetView.as_view(template_name='registration/password_reset.html'),
         name='password_reset'),
    path('password-reset/done/', 
         PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),
    # Add other routes as needed
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)