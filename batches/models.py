from django.db import models

class Batch(models.Model):
    department = models.ForeignKey(
        'departments.Department', 
        on_delete=models.CASCADE, 
        related_name='batches'
    )
    name = models.CharField(
        max_length=255, 
        help_text="e.g. 2027 Information Technology"
    )
    graduation_year = models.PositiveIntegerField(
        help_text="e.g. 2027"
    )
    semester = models.PositiveSmallIntegerField(
        default=1,
        help_text="Current Semester (e.g. 1 to 8)"
    )
    division = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g. Division A"
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['department', 'name'], 
                name='unique_department_batch_name'
            ),
        ]
        ordering = ['-graduation_year', 'name']

    def __str__(self):
        return f"{self.name} ({self.department.code})"
