from django import forms
from students.models import (
    Student, StudentSkill, Project, TechnicalLinks, Activity, WeeklySummary, MonthlySummary,
    ProjectMilestone, HackathonJournal, CodingPractice, LearningJournal, OpenSourceContribution,
    LearningGoal, DeveloperAchievement, Certificate, SemesterPerformance
)


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        exclude = ['student', 'created_at', 'updated_at']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Portfolio Builder'}),
            'short_description': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'Brief 1-sentence tagline'}),
            'detailed_description': forms.Textarea(attrs={'class': 'sp-form-input', 'rows': 4, 'placeholder': 'Detailed explanation of project architecture, functionality...'}),
            'category': forms.Select(attrs={'class': 'sp-form-input'}),
            'project_type': forms.Select(attrs={'class': 'sp-form-input'}),
            'status': forms.Select(attrs={'class': 'sp-form-input'}),
            'team_type': forms.Select(attrs={'class': 'sp-form-input'}),
            'start_date': forms.DateInput(attrs={'class': 'sp-form-input', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'sp-form-input', 'type': 'date'}),
            'technologies': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Python, Django, PostgreSQL (comma-separated)'}),
            'github_url': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'https://github.com/...'}),
            'live_url': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'https://...'}),
            'image': forms.FileInput(attrs={'class': 'sp-form-input', 'accept': 'image/*'}),
            'youtube_url': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'YouTube Demo Video URL'}),
            'documentation_url': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'Documentation website URL'}),
            'google_drive_url': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'Google Drive folder/report URL'}),
            'figma_url': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'Figma Design URL'}),
            'play_store_url': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'Google Play Store URL'}),
            'app_store_url': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'Apple App Store URL'}),
            'portfolio_url': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'Personal Portfolio URL'}),
            'key_features': forms.Textarea(attrs={'class': 'sp-form-input', 'rows': 3, 'placeholder': 'e.g. User Authentication, REST API, Payment Gateway (comma-separated)'}),
            'achievements': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Hackathon Winner, Published (comma-separated)'}),
            'is_featured': forms.CheckboxInput(attrs={'style': 'margin-right: 0.5rem; transform: scale(1.15);'}),
        }


class StudentSkillForm(forms.ModelForm):
    """Form for adding / editing a StudentSkill entry."""

    class Meta:
        model  = StudentSkill
        fields = ['name', 'category', 'proficiency', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class':       'sp-form-input',
                'placeholder': 'e.g. Python, MySQL, Docker…',
                'autofocus':   True,
            }),
            'category': forms.Select(attrs={
                'class': 'sp-form-input',
            }),
            'proficiency': forms.Select(attrs={
                'class': 'sp-form-input',
            }),
            'description': forms.TextInput(attrs={
                'class':       'sp-form-input',
                'placeholder': 'Optional note e.g. 2 years experience, used in projects…',
            }),
        }
        labels = {
            'name':        'Skill Name',
            'category':    'Category',
            'proficiency': 'Proficiency Level',
            'description': 'Short Note (optional)',
        }


class ResumeUploadForm(forms.Form):
    """Form to upload a PDF Resume or CV."""
    resume_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'sp-form-input',
            'placeholder': 'e.g. Full Stack Developer Resume (optional)'
        }),
        label='Resume Name'
    )
    resume_type = forms.ChoiceField(
        choices=[('RESUME', 'Resume'), ('CV', 'CV')],
        widget=forms.Select(attrs={'class': 'sp-form-input'}),
        label='Resume Type'
    )
    is_default = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'style': 'transform: scale(1.2); margin-right: 0.5rem;'}),
        label='Set as Default Resume'
    )
    file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'sp-form-input', 'accept': '.pdf'}),
        label='Choose PDF File'
    )

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # 1. Extension check
            if not file.name.lower().endswith('.pdf'):
                raise forms.ValidationError("Only PDF documents are allowed.")
            # 2. File size check (5 MB)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size must be under 5 MB.")
        return file


# ─────────────────────────────────────────────────────────────────────────────
# TechnicalLinksForm
# ─────────────────────────────────────────────────────────────────────────────

class TechnicalLinksForm(forms.ModelForm):
    class Meta:
        model = TechnicalLinks
        exclude = ['student']
        widgets = {
            'github': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'https://github.com/username'}),
            'leetcode': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'https://leetcode.com/username'}),
            'codechef': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'https://www.codechef.com/users/username'}),
            'codeforces': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'https://codeforces.com/profile/username'}),
            'hackerrank': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'https://www.hackerrank.com/username'}),
            'geeksforgeeks': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'https://auth.geeksforgeeks.org/user/username'}),
            'kaggle': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'https://www.kaggle.com/username'}),
            'portfolio': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'https://yourportfolio.com'}),
            'linkedin': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'https://linkedin.com/in/username'}),
        }


# ─────────────────────────────────────────────────────────────────────────────
# ActivityForm (Daily Log & Generic Updates)
# ─────────────────────────────────────────────────────────────────────────────

class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['title', 'description', 'category', 'date', 'hours_spent', 'technology_tags', 'status', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Solved 5 LeetCode Problems'}),
            'description': forms.Textarea(attrs={'class': 'sp-form-input', 'rows': 4, 'placeholder': 'e.g. Practiced Binary Trees DFS and dynamic programming...'}),
            'category': forms.Select(attrs={'class': 'sp-form-input'}),
            'date': forms.DateInput(attrs={'class': 'sp-form-input', 'type': 'date'}),
            'hours_spent': forms.NumberInput(attrs={'class': 'sp-form-input', 'min': 0, 'step': '0.1'}),
            'technology_tags': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Python, Algorithms (comma-separated)'}),
            'status': forms.Select(attrs={'class': 'sp-form-input'}),
            'attachment': forms.FileInput(attrs={'class': 'sp-form-input'}),
        }


# ─────────────────────────────────────────────────────────────────────────────
# WeeklySummaryForm
# ─────────────────────────────────────────────────────────────────────────────

class WeeklySummaryForm(forms.ModelForm):
    class Meta:
        model = WeeklySummary
        exclude = ['student']
        widgets = {
            'week_number': forms.NumberInput(attrs={'class': 'sp-form-input', 'min': 1, 'placeholder': 'e.g. 1, 2'}),
            'summary': forms.Textarea(attrs={'class': 'sp-form-input', 'rows': 4, 'placeholder': 'Detail your coding progress and milestones...'}),
            'hours': forms.NumberInput(attrs={'class': 'sp-form-input', 'min': 0, 'step': '0.1'}),
            'problems_solved': forms.NumberInput(attrs={'class': 'sp-form-input', 'min': 0}),
            'projects_worked': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. PlaceSync Dashboard, Compiler Design'}),
            'skills_learned': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Django ORM, REST API (comma-separated)'}),
            'challenges': forms.Textarea(attrs={'class': 'sp-form-input', 'rows': 3, 'placeholder': 'e.g. Debugging database deadlocks...'}),
            'date': forms.DateInput(attrs={'class': 'sp-form-input', 'type': 'date'}),
        }


# ─────────────────────────────────────────────────────────────────────────────
# MonthlySummaryForm
# ─────────────────────────────────────────────────────────────────────────────

class MonthlySummaryForm(forms.ModelForm):
    class Meta:
        model = MonthlySummary
        exclude = ['student']
        widgets = {
            'month': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. January 2026'}),
            'achievements': forms.Textarea(attrs={'class': 'sp-form-input', 'rows': 3, 'placeholder': 'Key milestones reached...'}),
            'projects_completed': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Recommendation Engine'}),
            'technologies_learned': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. PyTorch, Docker (comma-separated)'}),
            'certificates': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. AWS Cloud Practitioner'}),
            'goals': forms.Textarea(attrs={'class': 'sp-form-input', 'rows': 3, 'placeholder': 'Goals achieved or set...'}),
            'date': forms.DateInput(attrs={'class': 'sp-form-input', 'type': 'date'}),
        }


# ─────────────────────────────────────────────────────────────────────────────
# ProjectMilestoneForm
# ─────────────────────────────────────────────────────────────────────────────

class ProjectMilestoneForm(forms.ModelForm):
    class Meta:
        model = ProjectMilestone
        exclude = ['student']
        widgets = {
            'project': forms.Select(attrs={'class': 'sp-form-input'}),
            'milestone': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Build Login Module'}),
            'progress_pct': forms.NumberInput(attrs={'class': 'sp-form-input', 'min': 0, 'max': 100, 'placeholder': 'e.g. 50'}),
            'hours': forms.NumberInput(attrs={'class': 'sp-form-input', 'min': 0, 'step': '0.1'}),
            'technologies': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. HTML, CSS, Django (comma-separated)'}),
            'status': forms.Select(attrs={'class': 'sp-form-input'}),
            'date': forms.DateInput(attrs={'class': 'sp-form-input', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
        if student:
            # Only list student's own projects
            self.fields['project'].queryset = Project.objects.filter(student=student)


# ─────────────────────────────────────────────────────────────────────────────
# HackathonJournalForm
# ─────────────────────────────────────────────────────────────────────────────

class HackathonJournalForm(forms.ModelForm):
    class Meta:
        model = HackathonJournal
        exclude = ['student']
        widgets = {
            'hackathon_name': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Smart India Hackathon'}),
            'organizer': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Ministry of Education'}),
            'date': forms.DateInput(attrs={'class': 'sp-form-input', 'type': 'date'}),
            'theme': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Fintech Solutions'}),
            'team': forms.Textarea(attrs={'class': 'sp-form-input', 'rows': 2, 'placeholder': 'e.g. Team Lead: John, Backend: Bob...'}),
            'role': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Lead Backend Engineer'}),
            'project': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. PlaceSync App'}),
            'technologies': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Python, PostgreSQL (comma-separated)'}),
            'challenges': forms.Textarea(attrs={'class': 'sp-form-input', 'rows': 3, 'placeholder': 'Describe technical difficulties and debugging...'}),
            'learning': forms.Textarea(attrs={'class': 'sp-form-input', 'rows': 3, 'placeholder': 'What did you learn?'}),
            'achievement': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. 1st Place Winner, Runner Up'}),
            'certificate': forms.FileInput(attrs={'class': 'sp-form-input'}),
            'repository': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'GitHub repository link'}),
            'presentation': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'Figma, SlideShare or drive link'}),
            'photo': forms.FileInput(attrs={'class': 'sp-form-input'}),
        }


# ─────────────────────────────────────────────────────────────────────────────
# CodingPracticeForm
# ─────────────────────────────────────────────────────────────────────────────

class CodingPracticeForm(forms.ModelForm):
    class Meta:
        model = CodingPractice
        exclude = ['student']
        widgets = {
            'platform': forms.Select(attrs={'class': 'sp-form-input'}),
            'problems_solved': forms.NumberInput(attrs={'class': 'sp-form-input', 'min': 1}),
            'difficulty': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. 3 Easy, 2 Medium'}),
            'topics': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. DFS, BFS, Dynamic Programming'}),
            'notes': forms.Textarea(attrs={'class': 'sp-form-input', 'rows': 3, 'placeholder': 'e.g. Solved with O(N) complexity using hash map...'}),
            'date': forms.DateInput(attrs={'class': 'sp-form-input', 'type': 'date'}),
        }


# ─────────────────────────────────────────────────────────────────────────────
# LearningJournalForm
# ─────────────────────────────────────────────────────────────────────────────

class LearningJournalForm(forms.ModelForm):
    class Meta:
        model = LearningJournal
        exclude = ['student']
        widgets = {
            'course': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Machine Learning Specialization'}),
            'platform': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Coursera, Udemy'}),
            'duration': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. 12 hours, 3 weeks'}),
            'progress': forms.NumberInput(attrs={'class': 'sp-form-input', 'min': 0, 'max': 100, 'placeholder': 'Progress %'}),
            'topics': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Linear Regression, Neural Networks'}),
            'certificate': forms.FileInput(attrs={'class': 'sp-form-input'}),
            'notes': forms.Textarea(attrs={'class': 'sp-form-input', 'rows': 4, 'placeholder': 'Optimal solutions and structures learned...'}),
            'date': forms.DateInput(attrs={'class': 'sp-form-input', 'type': 'date'}),
        }


# ─────────────────────────────────────────────────────────────────────────────
# OpenSourceContributionForm
# ─────────────────────────────────────────────────────────────────────────────

class OpenSourceContributionForm(forms.ModelForm):
    class Meta:
        model = OpenSourceContribution
        exclude = ['student']
        widgets = {
            'repository': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. django/django'}),
            'contribution': forms.Textarea(attrs={'class': 'sp-form-input', 'rows': 3, 'placeholder': 'Describe code contributed...'}),
            'pull_request': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'https://github.com/django/django/pull/...'}),
            'issue': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'https://github.com/django/django/issues/...'}),
            'date': forms.DateInput(attrs={'class': 'sp-form-input', 'type': 'date'}),
            'learning': forms.Textarea(attrs={'class': 'sp-form-input', 'rows': 2, 'placeholder': 'Learned codebase styling/standards...'}),
        }


# ─────────────────────────────────────────────────────────────────────────────
# LearningGoalForm
# ─────────────────────────────────────────────────────────────────────────────

class LearningGoalForm(forms.ModelForm):
    class Meta:
        model = LearningGoal
        exclude = ['student']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Learn System Design basics'}),
            'priority': forms.Select(attrs={'class': 'sp-form-input'}),
            'target_date': forms.DateInput(attrs={'class': 'sp-form-input', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'sp-form-input'}),
        }


# ─────────────────────────────────────────────────────────────────────────────
# DeveloperAchievementForm
# ─────────────────────────────────────────────────────────────────────────────

class DeveloperAchievementForm(forms.ModelForm):
    class Meta:
        model = DeveloperAchievement
        exclude = ['student']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Research Publication in IEEE'}),
            'category': forms.Select(attrs={'class': 'sp-form-input'}),
            'date': forms.DateInput(attrs={'class': 'sp-form-input', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'sp-form-input', 'rows': 4, 'placeholder': 'Provide context, link, or verification details...'}),
            'certificate': forms.FileInput(attrs={'class': 'sp-form-input'}),
        }


# ─────────────────────────────────────────────────────────────────────────────
# CertificateForm
# ─────────────────────────────────────────────────────────────────────────────

class CertificateForm(forms.ModelForm):
    class Meta:
        model = Certificate
        exclude = ['student', 'created_at']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. AWS Certified Solutions Architect'}),
            'issuing_organization': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Amazon Web Services (AWS)'}),
            'category': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Cloud Computing, Web Development'}),
            'purpose': forms.Select(attrs={'class': 'sp-form-input'}),
            'credential_id': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. AWS-948201'}),
            'issue_date': forms.DateInput(attrs={'class': 'sp-form-input', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'sp-form-input', 'type': 'date'}),
            'certificate_url': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'Optional URL link to verify credential'}),
            'certificate_file': forms.FileInput(attrs={'class': 'sp-form-input', 'accept': '.pdf,image/*'}),
        }

    def clean_certificate_file(self):
        file = self.cleaned_data.get('certificate_file')
        if file:
            # 1. Extension check
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.webp']
            ext = '.' + file.name.lower().split('.')[-1]
            if ext not in allowed_extensions:
                raise forms.ValidationError("Only PDF documents and image files (JPG, PNG, WEBP) are allowed.")
            # 2. File size check (5 MB)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Certificate file size must be under 5 MB.")
        return file


# ─────────────────────────────────────────────────────────────────────────────
# CareerProfileForm
# ─────────────────────────────────────────────────────────────────────────────

class CareerProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'preferred_job_role', 'preferred_industry', 'preferred_city', 'preferred_country',
            'work_preference', 'expected_salary', 'career_objective', 'higher_studies',
            'willing_to_relocate'
        ]
        widgets = {
            'preferred_job_role': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Full Stack Developer, Data Scientist'}),
            'preferred_industry': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Information Technology, FinTech, E-commerce'}),
            'preferred_city': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Bangalore, Pune, Mumbai'}),
            'preferred_country': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. India, USA, Germany'}),
            'work_preference': forms.Select(attrs={'class': 'sp-form-input'}),
            'expected_salary': forms.NumberInput(attrs={'class': 'sp-form-input', 'step': '0.5', 'placeholder': 'Expected LPA e.g. 8.5'}),
            'career_objective': forms.Select(attrs={'class': 'sp-form-input'}),
            'higher_studies': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'Optional: e.g. MS in Computer Science'}),
            'willing_to_relocate': forms.CheckboxInput(attrs={'style': 'margin-right: 0.5rem; transform: scale(1.15);'}),
        }


# ─────────────────────────────────────────────────────────────────────────────
# PersonalProfileForm
# ─────────────────────────────────────────────────────────────────────────────

class PersonalProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'photo', 'name', 'email', 'phone', 'date_of_birth', 'gender', 'address',
            'github_url', 'linkedin_url', 'portfolio_url', 'leetcode_url',
            'bio', 'preferred_job_role', 'preferred_work_location', 'higher_studies'
        ]
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'sp-form-input', 'accept': 'image/*'}),
            'name': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'sp-form-input', 'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'Phone Number'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'sp-form-input', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'sp-form-input'}, choices=[
                ('', 'Select Gender'),
                ('Male', 'Male'),
                ('Female', 'Female'),
                ('Other', 'Other')
            ]),
            'address': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'Full Contact Address'}),
            'github_url': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'https://github.com/username'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'https://linkedin.com/in/username'}),
            'portfolio_url': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'https://portfolio.com'}),
            'leetcode_url': forms.URLInput(attrs={'class': 'sp-form-input', 'placeholder': 'https://leetcode.com/username'}),
            'bio': forms.Textarea(attrs={'class': 'sp-form-input', 'rows': 4, 'placeholder': 'Write a short professional summary...'}),
            'preferred_job_role': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Software Engineer, Data Analyst'}),
            'preferred_work_location': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Bangalore, Pune, Remote'}),
            'higher_studies': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'Optional: e.g. M.Tech, MS in CS'}),
        }


# ─────────────────────────────────────────────────────────────────────────────
# AcademicProfileForm
# ─────────────────────────────────────────────────────────────────────────────

class AcademicProfileForm(forms.ModelForm):
    # Dynamic decimal fields for 8 semesters
    spi_sem_1 = forms.DecimalField(max_digits=4, decimal_places=2, required=False, min_value=0.0, max_value=10.0, widget=forms.NumberInput(attrs={'class': 'sp-form-input', 'step': '0.01', 'placeholder': '--'}))
    spi_sem_2 = forms.DecimalField(max_digits=4, decimal_places=2, required=False, min_value=0.0, max_value=10.0, widget=forms.NumberInput(attrs={'class': 'sp-form-input', 'step': '0.01', 'placeholder': '--'}))
    spi_sem_3 = forms.DecimalField(max_digits=4, decimal_places=2, required=False, min_value=0.0, max_value=10.0, widget=forms.NumberInput(attrs={'class': 'sp-form-input', 'step': '0.01', 'placeholder': '--'}))
    spi_sem_4 = forms.DecimalField(max_digits=4, decimal_places=2, required=False, min_value=0.0, max_value=10.0, widget=forms.NumberInput(attrs={'class': 'sp-form-input', 'step': '0.01', 'placeholder': '--'}))
    spi_sem_5 = forms.DecimalField(max_digits=4, decimal_places=2, required=False, min_value=0.0, max_value=10.0, widget=forms.NumberInput(attrs={'class': 'sp-form-input', 'step': '0.01', 'placeholder': '--'}))
    spi_sem_6 = forms.DecimalField(max_digits=4, decimal_places=2, required=False, min_value=0.0, max_value=10.0, widget=forms.NumberInput(attrs={'class': 'sp-form-input', 'step': '0.01', 'placeholder': '--'}))
    spi_sem_7 = forms.DecimalField(max_digits=4, decimal_places=2, required=False, min_value=0.0, max_value=10.0, widget=forms.NumberInput(attrs={'class': 'sp-form-input', 'step': '0.01', 'placeholder': '--'}))
    spi_sem_8 = forms.DecimalField(max_digits=4, decimal_places=2, required=False, min_value=0.0, max_value=10.0, widget=forms.NumberInput(attrs={'class': 'sp-form-input', 'step': '0.01', 'placeholder': '--'}))

    class Meta:
        model = Student
        fields = [
            'college', 'department', 'course', 'batch',
            'current_academic_year', 'semester', 'admission_year', 'graduation_year',
            'tenth_board', 'tenth_percentage', 'twelfth_board', 'twelfth_percentage'
        ]
        widgets = {
            'college': forms.Select(attrs={'class': 'sp-form-input'}),
            'department': forms.Select(attrs={'class': 'sp-form-input'}),
            'course': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Computer Science & Engineering'}),
            'batch': forms.Select(attrs={'class': 'sp-form-input'}),
            'current_academic_year': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. 3rd Year'}),
            'semester': forms.NumberInput(attrs={'class': 'sp-form-input', 'min': 1, 'max': 8}),
            'admission_year': forms.NumberInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. 2023'}),
            'graduation_year': forms.NumberInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. 2027'}),
            'tenth_board': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. CBSE, ICSE'}),
            'tenth_percentage': forms.NumberInput(attrs={'class': 'sp-form-input', 'step': '0.01', 'placeholder': 'e.g. 92.50'}),
            'twelfth_board': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. CBSE, State Board'}),
            'twelfth_percentage': forms.NumberInput(attrs={'class': 'sp-form-input', 'step': '0.01', 'placeholder': 'e.g. 88.00'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Disable/Read-only seeded fields if they are not empty (Admin CSV import protection)
        if self.instance and self.instance.pk:
            # Check fields:
            if self.instance.college_id:
                self.fields['college'].disabled = True
                self.fields['college'].required = False
            if self.instance.department_id:
                self.fields['department'].disabled = True
                self.fields['department'].required = False
            if self.instance.course:
                self.fields['course'].disabled = True
                self.fields['course'].required = False
            if self.instance.batch_id:
                self.fields['batch'].disabled = True
                self.fields['batch'].required = False
            if self.instance.semester:
                self.fields['semester'].disabled = True
                self.fields['semester'].required = False
            if self.instance.admission_year:
                self.fields['admission_year'].disabled = True
                self.fields['admission_year'].required = False
            if self.instance.graduation_year:
                self.fields['graduation_year'].disabled = True
                self.fields['graduation_year'].required = False

            # Populate initial SPI values from database
            for sem in range(1, 9):
                perf = self.instance.semester_performances.filter(semester=sem).first()
                if perf:
                    self.initial[f'spi_sem_{sem}'] = perf.spi

    def save(self, commit=True):
        student = super().save(commit=False)
        if commit:
            student.save()
        
        # Save semester performance records
        spis = []
        for sem in range(1, 9):
            spi_val = self.cleaned_data.get(f'spi_sem_{sem}')
            if spi_val is not None:
                spis.append(float(spi_val))
                # Set status: Completed if sem < student.semester, Current if sem == student.semester, Upcoming if sem > student.semester
                if sem < student.semester:
                    status_val = "Completed"
                elif sem == student.semester:
                    status_val = "Current"
                else:
                    status_val = "Upcoming"
                
                perf, created = SemesterPerformance.objects.get_or_create(
                    student=student,
                    semester=sem,
                    defaults={'spi': spi_val, 'status': status_val}
                )
                if not created:
                    perf.spi = spi_val
                    perf.status = status_val
                    perf.save()
            else:
                # If SPI is blank, delete it
                student.semester_performances.filter(semester=sem).delete()

        # Recalculate CGPA from SPIs using Python
        if spis:
            from decimal import Decimal
            student.cgpa = Decimal(str(round(sum(spis) / len(spis), 2)))
        else:
            student.cgpa = None

        if commit:
            student.save()
        return student


class CareerProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'preferred_job_role', 'preferred_industry', 'preferred_city', 'preferred_country',
            'work_preference', 'willing_to_relocate', 'expected_salary', 'career_objective', 'higher_studies'
        ]
        widgets = {
            'preferred_job_role': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Full Stack Developer, Software Engineer'}),
            'preferred_industry': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Information Technology, FinTech'}),
            'preferred_city': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. Bangalore, Pune, Remote'}),
            'preferred_country': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. India'}),
            'work_preference': forms.Select(attrs={'class': 'sp-form-input'}),
            'willing_to_relocate': forms.CheckboxInput(attrs={'style': 'transform: scale(1.2); margin-right: 0.5rem;'}),
            'expected_salary': forms.NumberInput(attrs={'class': 'sp-form-input', 'step': '0.1', 'placeholder': 'e.g. 12.50'}),
            'career_objective': forms.Select(attrs={'class': 'sp-form-input'}),
            'higher_studies': forms.TextInput(attrs={'class': 'sp-form-input', 'placeholder': 'e.g. MS in CS, MBA'}),
        }



