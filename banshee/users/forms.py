from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from training.models import Senior

class SignupForm(UserCreationForm):
    passkey = forms.CharField(required=True)
    senior = forms.ChoiceField(choices=Senior.get_available_seniors)

    class Meta:
        model = User
        fields = ['username', 'passkey', 'email', 'password1', 'password2']
        labels = {'passkey': 'Passkey'}

    def clean(self):
        cleaned_data = self.cleaned_data
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')
        passkey = cleaned_data.get('passkey')

        if username and email and passkey:
            # Check Username and Email Uniqueness
            if User.objects.filter(username=username).exists():
                raise ValidationError({'username': "An Account with this Username Already Exists"})
            if User.objects.filter(email=email).exists():
                raise ValidationError({'email': "An Account with this Email Already Exists"})
            if not passkey == 'passkey':
                raise ValidationError({'passkey': "Passkey is Incorrect"})

        return cleaned_data
    
    def save(self, commit=True):
        print('[SENIOR CLEAN] ' + self.cleaned_data.get('senior'))
        return super().save(commit)
    