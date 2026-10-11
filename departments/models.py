from django.db import models

class Department(models.Model):
    college = models.ForeignKey(
        'colleges.College', 
        on_delete=models.CASCADE, 
        related_name='departments'
    )
    name = models.CharField(max_length=255)
    code = models.CharField(
        max_length=50, 
        help_text="e.g. CSE, ECE, ME"
    )
    description = models.TextField(blank=True)
    department_head = models.CharField(
        max_length=255,
        blank=True,
        help_text="Name of Head of Department"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['college', 'code'], 
                name='unique_college_department_code'
            ),
            models.UniqueConstraint(
                fields=['college', 'name'], 
                name='unique_college_department_name'
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.code}) - {self.college.code}"
