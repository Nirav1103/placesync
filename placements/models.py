from django.db import models

class PlacementDrive(models.Model):
    class Status(models.TextChoices):
        UPCOMING = 'UPCOMING', 'Upcoming'
        ACTIVE = 'ACTIVE', 'Active'
        COMPLETED = 'COMPLETED', 'Completed'

    class DriveType(models.TextChoices):
        JOB = 'JOB', 'Job Drive'
        INTERNSHIP = 'INTERNSHIP', 'Internship Drive'

    college = models.ForeignKey(
        'colleges.College', 
        on_delete=models.CASCADE, 
        related_name='placement_drives'
    )
    company = models.ForeignKey(
        'companies.Company', 
        on_delete=models.CASCADE, 
        related_name='placement_drives'
    )
    role = models.CharField(max_length=255)
    drive_type = models.CharField(
        max_length=20,
        choices=DriveType.choices,
        default=DriveType.JOB
    )
    package_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Package in LPA (or Stipend per month for internships)"
    )
    job_mode = models.CharField(
        max_length=20,
        choices=[
            ('REMOTE', 'Remote'),
            ('HYBRID', 'Hybrid'),
            ('ON_SITE', 'On-site')
        ],
        default='ON_SITE'
    )
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    
    # Eligibility Criteria
    min_cgpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0.00,
        help_text="Minimum CGPA required"
    )
    max_backlogs = models.PositiveIntegerField(
        default=0,
        help_text="Maximum active backlogs allowed"
    )
    eligible_departments = models.ManyToManyField(
        'departments.Department',
        related_name='eligible_drives',
        blank=True
    )
    eligible_batches = models.ManyToManyField(
        'batches.Batch',
        related_name='eligible_drives',
        blank=True
    )
    required_skills = models.TextField(
        blank=True,
        help_text="Comma-separated required skills (e.g. Python, SQL)"
    )
    
    # Selection Process
    selection_process = models.TextField(
        blank=True,
        help_text="Details of selection rounds (e.g. Resume Shortlisting -> Test -> Technical -> HR)"
    )

    # Additional Post Details
    location = models.CharField(
        max_length=255,
        blank=True,
        help_text="Job/Internship location"
    )

    class EmploymentType(models.TextChoices):
        FULL_TIME = 'FULL_TIME', 'Full Time'
        PART_TIME = 'PART_TIME', 'Part Time'
        CONTRACT = 'CONTRACT', 'Contract'
        FREELANCE = 'FREELANCE', 'Freelance'

    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME
    )
    vacancies = models.PositiveIntegerField(
        default=1,
        help_text="Number of open positions"
    )
    job_description = models.TextField(
        blank=True,
        help_text="Full description of the role"
    )
    responsibilities = models.TextField(
        blank=True,
        help_text="Key responsibilities for the role"
    )
    attachment = models.FileField(
        upload_to='drive_attachments/',
        blank=True,
        null=True,
        help_text="Optional supporting document (PDF, DOCX)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_drive_type_display()} - {self.role} ({self.company.name})"


class Application(models.Model):
    class ApplicationStatus(models.TextChoices):
        APPLIED = 'APPLIED', 'Applied'
        SHORTLISTED = 'SHORTLISTED', 'Shortlisted'
        SELECTED = 'SELECTED', 'Selected'
        REJECTED = 'REJECTED', 'Rejected'

    drive = models.ForeignKey(
        PlacementDrive,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='applications'
    )
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.APPLIED
    )
    resume = models.FileField(
        upload_to='student_resumes/',
        blank=True,
        null=True,
        help_text="Custom resume for this application"
    )
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['drive', 'student'],
                name='unique_drive_student_application'
            )
        ]
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.student.user.username} application to {self.drive}"


# ─────────────────────────────────────────────────────────────────────────────
# DriveBookmark — tracks student bookmarks for placement drives
# ─────────────────────────────────────────────────────────────────────────────

class DriveBookmark(models.Model):
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='drive_bookmarks'
    )
    drive = models.ForeignKey(
        PlacementDrive,
        on_delete=models.CASCADE,
        related_name='bookmarked_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'drive'],
                name='unique_student_drive_bookmark'
            )
        ]

    def __str__(self):
        return f"{self.student.name} bookmarked {self.drive}"


# ─────────────────────────────────────────────────────────────────────────────
# PlacementCalendarEvent — tracks timeline events for applied drives
# ─────────────────────────────────────────────────────────────────────────────

class PlacementCalendarEvent(models.Model):
    class EventType(models.TextChoices):
        DEADLINE = 'DEADLINE', 'Application Deadline'
        APTITUDE_TEST = 'APTITUDE_TEST', 'Aptitude Test'
        TECH_INTERVIEW = 'TECH_INTERVIEW', 'Technical Interview'
        HR_INTERVIEW = 'HR_INTERVIEW', 'HR Interview'
        OFFER_RELEASE = 'OFFER_RELEASE', 'Offer Release'
        JOINING_DATE = 'JOINING_DATE', 'Joining Date'

    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='calendar_events'
    )
    drive = models.ForeignKey(
        PlacementDrive,
        on_delete=models.CASCADE,
        related_name='calendar_events'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_date = models.DateField()
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        default=EventType.DEADLINE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['event_date', 'event_type']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'drive', 'event_type'],
                name='unique_student_drive_event_type'
            )
        ]

    def __str__(self):
        return f"{self.title} on {self.event_date} ({self.get_event_type_display()})"

