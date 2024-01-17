from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django_countries.fields import Country, CountryField
from account.constants import *
from account.models import Client, KYC

User = get_user_model()


class SignUpForm(forms.ModelForm):
    """sign up form"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': (
                    'form-control '

                )
            })
    account_type = forms.ChoiceField(label='account type', choices=account_type)
    transaction_pin = forms.CharField(max_length=6)
    mobile = forms.CharField(max_length=15)
    country = CountryField(blank_label='(select country)', blank=False).formfield()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)


    class Meta:
        model = User
        fields = ['email', 'name']

    def clean_mobile(self):
        mobile = self.cleaned_data['mobile']
        if Client.objects.filter(mobile=mobile).exists():
            raise forms.ValidationError("Mobile number already exists")
        return mobile

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password1'] != cd['password2']:
            raise forms.ValidationError('Passwords do not match.')
        return cd['password2']

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                'Please use another Email, this is already taken')
        return email


class PwdResetForm(PasswordResetForm):

    def clean_email(self):
        email = self.cleaned_data['email']
        user = User.objects.filter(email=email)
        if not user:
            raise forms.ValidationError(
                'Unfortunately we can not find that email address')
        return email



class VerificationForm(forms.ModelForm):
    class Meta:
        model = KYC
        fields = ['first_name', 'last_name', 'dob', 'gender', 'postcode', 'address', 'id_front_view',  'document_type',
                  'state', 'town_city', 'id_back_view', 'ssn']


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': (
                    'form-control '

                )
            })
