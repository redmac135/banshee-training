from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from training.models import Senior, PO

class UserForm(UserCreationForm):
    passkey = forms.CharField(max_length=10)

    class Meta:
        model = User
        fields = ['username', 'passkey', 'first_name', 'last_name', 'email', 'password1', 'password2']

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

class SeniorForm(forms.ModelForm):
    preferences = forms.MultipleChoiceField(choices=PO.get_choice_tuples(), widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = Senior
        fields = ['preferences']