from django.db import models
from django.conf import settings

class EmailTemplate(models.Model):
    college = models.ForeignKey(
        'colleges.College',
        on_delete=models.CASCADE,
        related_name='email_templates'
    )
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    body = models.TextField(help_text="Supports template placeholders like {{ student_name }} or {{ company_name }}.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['college', 'name'],
                name='unique_college_template_name'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.college.code})"


class SentEmail(models.Model):
    class RecipientType(models.TextChoices):
        STUDENTS = 'STUDENTS', 'Eligible Students'
        COMPANIES = 'COMPANIES', 'Partner Companies'
        CUSTOM = 'CUSTOM', 'Custom Email List'

    class SendStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending (Scheduled)'
        SENT = 'SENT', 'Sent'
        FAILED = 'FAILED', 'Failed'

    college = models.ForeignKey(
        'colleges.College',
        on_delete=models.CASCADE,
        related_name='sent_emails'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_emails'
    )
    recipient_type = models.CharField(
        max_length=20,
        choices=RecipientType.choices,
        default=RecipientType.CUSTOM
    )
    recipients = models.TextField(help_text="Comma-separated list of target emails")
    subject = models.CharField(max_length=255)
    body = models.TextField()
    attachment = models.FileField(
        upload_to='email_attachments/',
        blank=True,
        null=True
    )
    scheduled_time = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Leave blank to send immediately"
    )
    status = models.CharField(
        max_length=20,
        choices=SendStatus.choices,
        default=SendStatus.SENT
    )
    sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} to {self.get_recipient_type_display()} ({self.get_status_display()})"


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} for {self.user.username} (Read: {self.is_read})"
