from django import forms
from .models import Batch
from departments.models import Department

class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['department', 'name', 'graduation_year', 'semester', 'division', 'description']
        widgets = {
            'graduation_year': forms.NumberInput(attrs={'placeholder': 'e.g. 2027'}),
            'name': forms.TextInput(attrs={'placeholder': 'e.g. 2027 Information Technology'}),
            'semester': forms.NumberInput(attrs={'placeholder': 'e.g. 8', 'min': 1, 'max': 8}),
            'division': forms.TextInput(attrs={'placeholder': 'e.g. A'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional brief description'}),
        }

    def __init__(self, *args, **kwargs):
        self.college = kwargs.pop('college', None)
        super().__init__(*args, **kwargs)
        
        # Style form fields
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-input'})

        # Filter department select queryset based on college
        if self.college:
            self.fields['department'].queryset = Department.objects.filter(college=self.college).order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        dept = cleaned_data.get('department')
        if dept and name:
            qs = Batch.objects.filter(department=dept, name__iexact=name)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('name', "A batch with this name already exists in this department.")
        return cleaned_data
