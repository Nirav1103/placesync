from django.db import models
from django.conf import settings

class StaffMember(models.Model):
    class RoleChoices(models.TextChoices):
        EDITOR = 'EDITOR', 'Editor'
        VIEW_ONLY = 'VIEW_ONLY', 'View Only'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='staff_profile')
    college = models.ForeignKey('colleges.College', on_delete=models.CASCADE, related_name='staff_members')
    role = models.CharField(max_length=20, choices=RoleChoices.choices)
    profile_picture = models.ImageField(upload_to='staff_photos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"
