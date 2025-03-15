from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import TimeSlot

class CustomUserCreationForm(UserCreationForm):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('faculty', 'Faculty')
    ]
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'user_type']

class TimeSlotForm(forms.ModelForm):
    class Meta:
        model = TimeSlot
        fields = ['date', 'start_time', 'end_time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }