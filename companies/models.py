from django.db import models

class Company(models.Model):
    class JobMode(models.TextChoices):
        REMOTE = 'REMOTE', 'Remote'
        HYBRID = 'HYBRID', 'Hybrid'
        ON_SITE = 'ON_SITE', 'On-site'

    class VerificationStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        VERIFIED = 'VERIFIED', 'Verified'
        REJECTED = 'REJECTED', 'Rejected'

    college = models.ForeignKey(
        'colleges.College', 
        on_delete=models.CASCADE, 
        related_name='companies'
    )
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    website = models.URLField(blank=True)
    career_page = models.URLField(blank=True)
    industry = models.CharField(max_length=255, blank=True)
    company_size = models.CharField(max_length=100, blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    about_company = models.TextField(blank=True, null=True)
    registration_number = models.CharField(max_length=100, blank=True, null=True)
    
    # HR Details
    hr_name = models.CharField(max_length=255, blank=True)
    hr_email = models.EmailField(blank=True)
    hr_phone = models.CharField(max_length=20, blank=True)
    hr_notes = models.TextField(blank=True, help_text="Any additional HR contact details or notes")
    
    location = models.CharField(max_length=255, blank=True)
    
    # Placement Terms
    package_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        help_text="Package Offered (LPA) e.g. 12.50"
    )
    stipend_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        help_text="Monthly Stipend Offered e.g. 25000"
    )
    job_mode = models.CharField(
        max_length=20,
        choices=JobMode.choices,
        default=JobMode.ON_SITE
    )
    
    # Placement History
    placement_history = models.TextField(
        blank=True, 
        help_text="Summary of past recruits, years, and performance from this college"
    )
    
    # Company Verification Checks
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING
    )
    is_website_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    is_career_page_verified = models.BooleanField(default=False)
    is_address_verified = models.BooleanField(default=False)
    verification_notes = models.TextField(blank=True)
    trust_score = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['college', 'name'], 
                name='unique_college_company_name'
            ),
        ]
        ordering = ['name']

    def calculate_trust_score(self):
        score = 0
        if self.is_website_verified:
            score += 25
        if self.is_email_verified:
            score += 25
        if self.is_career_page_verified:
            score += 25
        if self.is_address_verified:
            score += 25
        return score

    def save(self, *args, **kwargs):
        self.trust_score = self.calculate_trust_score()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.college.code}"
