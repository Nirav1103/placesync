from django.db import models

class College(models.Model):
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=50, unique=True, help_text="Unique college code or abbreviation")
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Profile Enhancements
    logo = models.ImageField(upload_to='college_logos/', blank=True, null=True)
    university = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Social Handles
    linkedin = models.URLField(blank=True, verbose_name="LinkedIn")
    twitter = models.URLField(blank=True, verbose_name="Twitter")
    instagram = models.URLField(blank=True, verbose_name="Instagram")

    def __str__(self):
        return f"{self.name} ({self.code})"


class CampusImage(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='campus_images')
    image = models.ImageField(upload_to='campus_images/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Campus image for {self.college.code} - {self.id}"
