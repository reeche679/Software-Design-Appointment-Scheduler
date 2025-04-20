from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import TimeSlot, StudentFile, FileComment

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
        fields = ['date', 'start_time', 'end_time', 'room']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'room': forms.Select(attrs={'class': 'form-control'})
        }

class StudentFileForm(forms.ModelForm):
    class Meta:
        model = StudentFile
        fields = ['file_type', 'file', 'description']
        widgets = {
            'file_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'file': forms.FileInput(attrs={'class': 'form-control'})
        }

class FileCommentForm(forms.ModelForm):
    class Meta:
        model = FileComment
        fields = ['comment', 'is_private']
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter your comment here...'}),
            'is_private': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }