from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from accounts.models import Buyer, Farmer

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        # Map Google extra data if available
        if sociallogin.account.provider == 'google':
            extra_data = sociallogin.account.extra_data
            first_name = extra_data.get('given_name', '')
            last_name = extra_data.get('family_name', '')
            
            if not user.first_name and first_name:
                user.first_name = first_name
            if not user.last_name and last_name:
                user.last_name = last_name

        # Clear default role for new social users so they choose Farmer or Buyer
        user.role = ''
        user.save()

        return user


