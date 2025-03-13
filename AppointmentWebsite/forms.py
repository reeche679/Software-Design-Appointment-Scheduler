from django import forms
from .models import Appointment, TimeSlot

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['client_name', 'appointment_date', 'service']
    

class TimeSlotForm(forms.ModelForm):
    class Meta:
        model = TimeSlot
        fields = ['date', 'start_time', 'end_time', 'faculty']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }