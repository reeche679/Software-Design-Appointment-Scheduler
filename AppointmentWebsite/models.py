from django.db import models

# Create your models here.

class Appointment(models.Model):
    client_name = models.CharField(max_length=100)
    appointment_date = models.DateTimeField()
    service = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='Scheduled')

    def __str__(self):
        return f"{self.client_name} - {self.appointment_date.strftime('%Y-%m-%d %H:%M')}"
