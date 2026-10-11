from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from colleges.models import College

User = get_user_model()

class CollegeRegistrationForm(forms.Form):
    college_name = forms.CharField(
        max_length=255, 
        label="College Name",
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Stanford University'})
    )
    college_code = forms.CharField(
        max_length=50, 
        label="College Code (Abbreviation)",
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. SU'})
    )
    college_website = forms.URLField(
        label="College Website",
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://example.edu'})
    )
    username = forms.CharField(
        max_length=150,
        label="Admin Username",
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. stanford_admin'})
    )
    email = forms.EmailField(
        label="Admin Email",
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'e.g. admin@example.edu'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': '••••••••'})
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': '••••••••'})
    )

    def clean_college_name(self):
        name = self.cleaned_data.get('college_name')
        if College.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError("A college with this name is already registered.")
        return name

    def clean_college_code(self):
        code = self.cleaned_data.get('college_code')
        if College.objects.filter(code__iexact=code).exists():
            raise forms.ValidationError("A college with this code is already registered.")
        return code

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self):
        college = College.objects.create(
            name=self.cleaned_data['college_name'],
            code=self.cleaned_data['college_code'].upper(),
            website=self.cleaned_data['college_website']
        )
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            college=college,
            role=User.Role.COLLEGE_ADMIN
        )
        return user


class CollegeLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-input',
        'placeholder': 'Enter your username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input',
        'placeholder': '••••••••'
    }))
