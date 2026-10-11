from django import forms
from .models import PlacementDrive, Application
from companies.models import Company
from departments.models import Department

class PlacementDriveForm(forms.ModelForm):
    class Meta:
        model = PlacementDrive
        fields = [
            'company',
            'drive_type',
            'role',
            'package_amount',
            'job_mode',
            'min_cgpa',
            'max_backlogs',
            'eligible_departments',
            'deadline',
            'status',
            'selection_process'
        ]
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'min_cgpa': forms.NumberInput(attrs={'placeholder': 'e.g. 7.50', 'step': '0.01'}),
            'max_backlogs': forms.NumberInput(attrs={'placeholder': 'e.g. 0'}),
            'selection_process': forms.Textarea(attrs={'rows': 4, 'placeholder': 'e.g. Round 1: Coding Test, Round 2: Technical Interview, Round 3: HR Discussion'}),
            'eligible_departments': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        self.college = kwargs.pop('college', None)
        super().__init__(*args, **kwargs)
        
        if self.college:
            # Filter companies and departments by college
            self.fields['company'].queryset = Company.objects.filter(college=self.college).order_by('name')
            self.fields['eligible_departments'].queryset = Department.objects.filter(college=self.college).order_by('name')
            
        for name, field in self.fields.items():
            if name not in ['deadline', 'eligible_departments']:
                field.widget.attrs.update({'class': 'form-input'})


class StudentApplyForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['resume']
        widgets = {
            'resume': forms.FileInput(attrs={'class': 'form-input', 'style': 'padding: 0.5rem;'}),
        }
