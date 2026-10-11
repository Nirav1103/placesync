from django import forms
from .models import EmailTemplate, SentEmail
from batches.models import Batch
from departments.models import Department

class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ['name', 'subject', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 8, 'placeholder': 'Write email template body here. Use {{ student_name }} for student name placeholders.'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-input'})


class ComposeEmailForm(forms.Form):
    recipient_type = forms.ChoiceField(
        choices=SentEmail.RecipientType.choices,
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    target_batch = forms.ModelChoiceField(
        queryset=Batch.objects.none(),
        required=False,
        label="Target Student Batch",
        widget=forms.Select(attrs={'class': 'form-input'}),
        help_text="Optional. Only used if recipient type is 'Eligible Students'."
    )
    target_department = forms.ModelChoiceField(
        queryset=Department.objects.none(),
        required=False,
        label="Target Student Department",
        widget=forms.Select(attrs={'class': 'form-input'}),
        help_text="Optional. Only used if recipient type is 'Eligible Students'."
    )
    custom_recipients = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g. test1@gmail.com, test2@gmail.com', 'class': 'form-input'}),
        required=False,
        label="Custom Email Recipients",
        help_text="Required if recipient type is 'Custom Email List'."
    )
    template = forms.ModelChoiceField(
        queryset=EmailTemplate.objects.none(),
        required=False,
        label="Prefill using Template",
        widget=forms.Select(attrs={'class': 'form-input'}),
        help_text="Optional. Select an existing template to prefill the subject and body."
    )
    scheduled_time = forms.DateTimeField(
        required=False,
        label="Schedule Dispatch Time",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
        help_text="Optional. Leave blank to send immediately."
    )
    subject = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Enter email subject...', 'class': 'form-input'})
    )
    body = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 8, 'placeholder': 'Enter email body contents...', 'class': 'form-input'})
    )
    attachment = forms.FileField(
        required=False,
        label="File Attachment",
        widget=forms.FileInput(attrs={'class': 'form-input', 'style': 'padding: 0.5rem;'})
    )

    def __init__(self, *args, **kwargs):
        self.college = kwargs.pop('college', None)
        super().__init__(*args, **kwargs)
        
        if self.college:
            self.fields['target_batch'].queryset = Batch.objects.filter(department__college=self.college).order_by('name')
            self.fields['target_department'].queryset = Department.objects.filter(college=self.college).order_by('name')
            self.fields['template'].queryset = EmailTemplate.objects.filter(college=self.college).order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        recipient_type = cleaned_data.get('recipient_type')
        custom_recipients = cleaned_data.get('custom_recipients')
        
        if recipient_type == SentEmail.RecipientType.CUSTOM and not custom_recipients:
            self.add_error('custom_recipients', "Please specify recipient emails for the Custom List.")
            
        return cleaned_data
