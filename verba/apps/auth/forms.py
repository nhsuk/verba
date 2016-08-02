from django import forms
from django.contrib.auth import authenticate


class AuthenticationForm(forms.Form):
    code = forms.CharField(max_length=254)

    error_messages = {
        'invalid_login': "An error occurred when trying to log in"
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super(AuthenticationForm, self).__init__(*args, **kwargs)

    def clean(self):
        code = self.cleaned_data.get('code')

        self.user_cache = authenticate(code=code)
        if self.user_cache is None:
            raise forms.ValidationError(
                self.error_messages['invalid_login'],
                code='invalid_login',
            )
        return self.cleaned_data

    def get_user(self):
        return self.user_cache
