from django import forms
from .models import Department

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'department_head', 'description']
        widgets = {
            'department_head': forms.TextInput(attrs={'placeholder': 'Name of Head of Department'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional brief description'}),
        }

    def __init__(self, *args, **kwargs):
        self.college = kwargs.pop('college', None)
        super().__init__(*args, **kwargs)
        
        # Apply CSS styling class to form fields
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-input'})
            
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if self.college:
            qs = Department.objects.filter(college=self.college, name__iexact=name)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("A department with this name already exists in your college.")
        return name

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if self.college:
            qs = Department.objects.filter(college=self.college, code__iexact=code)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("A department with this code already exists in your college.")
        return code.upper()
