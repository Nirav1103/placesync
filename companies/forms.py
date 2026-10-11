from django import forms
from .models import Company

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            'name',
            'logo',
            'website',
            'career_page',
            'industry',
            'company_size',
            'linkedin_url',
            'about_company',
            'registration_number',
            'hr_name',
            'hr_email',
            'hr_phone',
            'hr_notes',
            'location',
            'package_amount',
            'stipend_amount',
            'job_mode',
            'placement_history'
        ]
        widgets = {
            'package_amount': forms.NumberInput(attrs={'placeholder': 'e.g. 12.50 (in LPA)'}),
            'stipend_amount': forms.NumberInput(attrs={'placeholder': 'e.g. 25000 (monthly)'}),
            'hr_notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g. Additional contact numbers, best time to call'}),
            'placement_history': forms.Textarea(attrs={'rows': 4, 'placeholder': 'e.g. 2025: 5 students recruited, 2026: 8 students recruited'}),
            'about_company': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Brief description about the company...'}),
        }

    def __init__(self, *args, **kwargs):
        self.college = kwargs.pop('college', None)
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != 'logo':
                field.widget.attrs.update({'class': 'form-input'})
            else:
                field.widget.attrs.update({'class': 'form-input', 'style': 'padding: 0.5rem;'})


    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError("Company name cannot be empty.")
        
        # Check unique constraint case-insensitively within the college
        qs = Company.objects.filter(college=self.college, name__iexact=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A company with this name is already registered in your college.")
        
        return name


class CompanyVerificationForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            'is_website_verified',
            'is_email_verified',
            'is_career_page_verified',
            'is_address_verified',
            'verification_status',
            'verification_notes'
        ]
        widgets = {
            'verification_notes': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Provide auditing comments or check references notes...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['verification_status'].widget.attrs.update({'class': 'form-input'})
        self.fields['verification_notes'].widget.attrs.update({'class': 'form-input'})
