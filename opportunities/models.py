from django.db import models

class ScrapedOpportunity(models.Model):
    class VerificationStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        VERIFIED = 'VERIFIED', 'Verified'
        IGNORED = 'IGNORED', 'Ignored'

    college = models.ForeignKey(
        'colleges.College', 
        on_delete=models.CASCADE, 
        related_name='scraped_opportunities'
    )
    company_name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    package = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    deadline = models.CharField(max_length=255, blank=True)
    source = models.URLField(max_length=500, blank=True)
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING
    )
    trust_score = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-trust_score', '-created_at']

    def calculate_trust_score(self):
        score = 0
        if self.company_name:
            score += 20
        if self.role:
            score += 20
        if self.location:
            score += 20
        if self.package:
            score += 15
        if self.deadline:
            score += 15
        if self.source:
            score += 10
        return score

    def save(self, *args, **kwargs):
        self.trust_score = self.calculate_trust_score()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.role} at {self.company_name} ({self.get_verification_status_display()})"
