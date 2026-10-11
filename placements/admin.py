from django.contrib import admin
from .models import PlacementDrive, Application, DriveBookmark, PlacementCalendarEvent


@admin.register(PlacementDrive)
class PlacementDriveAdmin(admin.ModelAdmin):
    list_display = ('role', 'company', 'drive_type', 'package_amount', 'deadline', 'status')
    list_filter = ('drive_type', 'status', 'college')
    search_fields = ('role', 'company__name')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'drive', 'status', 'applied_at')
    list_filter = ('status',)
    search_fields = ('student__name', 'drive__role', 'drive__company__name')


@admin.register(DriveBookmark)
class DriveBookmarkAdmin(admin.ModelAdmin):
    list_display = ('student', 'drive', 'created_at')
    search_fields = ('student__name', 'drive__role')


@admin.register(PlacementCalendarEvent)
class PlacementCalendarEventAdmin(admin.ModelAdmin):
    list_display = ('student', 'drive', 'title', 'event_date', 'event_type')
    list_filter = ('event_type',)
    search_fields = ('student__name', 'title')
