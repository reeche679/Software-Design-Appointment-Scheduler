from django import forms
from AppointmentWebsite.models import UserProfile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['user_type']
        widgets = {
            'user_type': forms.Select(choices=UserProfile._meta.get_field('user_type').choices)
        } 