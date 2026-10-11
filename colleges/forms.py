from django import forms
from .models import College, CampusImage

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class CollegeProfileForm(forms.ModelForm):
    campus_images = forms.FileField(
        widget=MultipleFileInput(attrs={'class': 'form-input'}),
        required=False,
        label="Upload Campus Images"
    )
    delete_images = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'delete-checkbox-list'}),
        required=False,
        label="Select Campus Images to Delete"
    )

    class Meta:
        model = College
        fields = ['name', 'university', 'address', 'website', 'email', 'phone', 'logo', 'linkedin', 'twitter', 'instagram']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g. 123 University Ave, Tech City'}),
            'logo': forms.FileInput(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply form-input classes dynamically to widgets
        for name, field in self.fields.items():
            if name not in ['logo', 'campus_images', 'delete_images']:
                field.widget.attrs.update({'class': 'form-input'})
            
        # Dynamically load choices for delete_images
        if self.instance and self.instance.pk:
            images = self.instance.campus_images.all()
            if images.exists():
                self.fields['delete_images'].choices = [
                    (img.id, img) for img in images
                ]
            else:
                self.fields.pop('delete_images', None)
        else:
            self.fields.pop('delete_images', None)
