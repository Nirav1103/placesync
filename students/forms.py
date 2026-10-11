from django import forms
from django.contrib.auth import get_user_model
from students.models import Student
from batches.models import Batch

User = get_user_model()

class StudentEditForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'roll_number', 
            'name', 
            'email', 
            'phone', 
            'placement_status', 
            'package_amount', 
            'stipend_amount'
        ]
        widgets = {
            'package_amount': forms.NumberInput(attrs={'placeholder': 'Package in LPA (if placed)'}),
            'stipend_amount': forms.NumberInput(attrs={'placeholder': 'Stipend /mo (if intern)'}),
        }

    def __init__(self, *args, **kwargs):
        self.college = kwargs.pop('college', None)
        super().__init__(*args, **kwargs)
        
        # Style form fields
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-input'})

    def clean_roll_number(self):
        roll_number = self.cleaned_data.get('roll_number', '').strip()
        if not roll_number:
            raise forms.ValidationError("Roll number cannot be empty.")
            
        # Check unique constraint within the college case-insensitively
        qs = Student.objects.filter(college=self.college, roll_number__iexact=roll_number)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A student with this roll number is already registered in this college.")

        # Check global User username uniqueness to prevent collision on saving
        user_qs = User.objects.filter(username__iexact=roll_number)
        if self.instance and self.instance.user:
            user_qs = user_qs.exclude(pk=self.instance.user.pk)
        if user_qs.exists():
            raise forms.ValidationError("This roll number (username) is already registered in the system.")

        return roll_number

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if not email:
            raise forms.ValidationError("Email cannot be empty.")
            
        # Check user database uniqueness case-insensitively
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.user:
            qs = qs.exclude(pk=self.instance.user.pk)
        if qs.exists():
            raise forms.ValidationError("This email is already registered in the system.")
        return email

    def save(self, commit=True):
        student = super().save(commit=False)
        
        # Update user fields
        if student.user:
            student.user.username = self.cleaned_data['roll_number'].strip()
            student.user.email = self.cleaned_data['email'].strip()
            if commit:
                student.user.save()
                
        if commit:
            student.save()
        return student


class StudentMoveForm(forms.Form):
    batch = forms.ModelChoiceField(
        queryset=Batch.objects.none(),
        label="Select Target Batch",
        empty_label="-- Select Batch --",
        widget=forms.Select(attrs={'class': 'form-input'})
    )

    def __init__(self, *args, **kwargs):
        self.college = kwargs.pop('college', None)
        super().__init__(*args, **kwargs)
        if self.college:
            self.fields['batch'].queryset = Batch.objects.filter(
                department__college=self.college
            ).order_by('-graduation_year', 'name')


class StudentResetPasswordForm(forms.Form):
    password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Enter new password'}),
        help_text="Min 6 characters. The student will be forced to change this password on their next login."
    )

    def clean_password(self):
        password = self.cleaned_data.get('password', '').strip()
        if len(password) < 6:
            raise forms.ValidationError("Password must be at least 6 characters long.")
        return password
