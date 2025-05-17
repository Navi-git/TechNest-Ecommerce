# userauths/forms.py
from django import forms
from userauths.models import User

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['profile_picture']
