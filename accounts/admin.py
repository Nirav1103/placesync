from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'college', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active', 'college')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Attributes', {'fields': ('role', 'college')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Attributes', {'fields': ('role', 'college')}),
    )
