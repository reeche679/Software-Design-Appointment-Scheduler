from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=[('student', 'Student'), ('faculty', 'Faculty')])
    
    def __str__(self):
        return f"{self.user.username} - {self.user_type}"

class TimeSlot(models.Model):
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    faculty = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_slots')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.faculty.username} - {self.date} ({self.start_time} - {self.end_time})"

class Appointment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    time_slot = models.OneToOneField(TimeSlot, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='Scheduled')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.student.username} - {self.time_slot}"