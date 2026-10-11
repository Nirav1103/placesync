from django import forms
from .models import ScrapedOpportunity

class ScrapedOpportunityForm(forms.ModelForm):
    class Meta:
        model = ScrapedOpportunity
        fields = ['company_name', 'role', 'package', 'location', 'deadline', 'source']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-input'})

class ScrapeUrlForm(forms.Form):
    url = forms.URLField(
        label="Target Career Page URL",
        widget=forms.URLInput(attrs={
            'class': 'form-input', 
            'placeholder': 'https://example.com/careers'
        })
    )
