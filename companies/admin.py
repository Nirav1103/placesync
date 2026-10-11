from django.contrib import admin
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'college', 'industry', 'company_size', 'verification_status', 'hr_name', 'hr_email', 'created_at')
    list_filter = ('college', 'verification_status', 'job_mode')
    search_fields = ('name', 'industry', 'hr_name', 'hr_email', 'location')
    readonly_fields = ('trust_score', 'created_at', 'updated_at')
    fieldsets = (
        ('Company Info', {
            'fields': ('college', 'name', 'logo', 'industry', 'company_size', 'location', 'website', 'linkedin_url', 'career_page', 'about_company', 'registration_number')
        }),
        ('HR Contact', {
            'fields': ('hr_name', 'hr_email', 'hr_phone', 'hr_notes')
        }),
        ('Placement Terms', {
            'fields': ('package_amount', 'stipend_amount', 'job_mode', 'placement_history')
        }),
        ('Verification', {
            'fields': ('verification_status', 'is_website_verified', 'is_email_verified', 'is_career_page_verified', 'is_address_verified', 'verification_notes', 'trust_score')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
