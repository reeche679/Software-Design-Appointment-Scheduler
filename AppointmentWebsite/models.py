from django.db import models
from django.contrib.auth.models import User


# Create your models here.

class Appointment(models.Model):
    client_name = models.CharField(max_length=100)
    appointment_date = models.DateTimeField()
    service = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='Scheduled')

    def __str__(self):
        return f"{self.client_name} - {self.appointment_date.strftime('%Y-%m-%d %H:%M')}"

class TimeSlot(models.Model):
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    faculty = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.faculty} - {self.date} ({self.start_time} - {self.end_time})"