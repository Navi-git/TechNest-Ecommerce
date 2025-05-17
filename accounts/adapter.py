# accounts/adapter.py

import requests
from django.core.files.base import ContentFile
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        # Only for Google logins
        if sociallogin.account.provider == 'google':
            extra_data = sociallogin.account.extra_data
            picture_url = extra_data.get('picture')

            if picture_url and not user.profile_picture:
                response = requests.get(picture_url)
                if response.status_code == 200:
                    file_name = f"{user.pk}_google.jpg"
                    user.profile_picture.save(file_name, ContentFile(response.content), save=True)

        return user