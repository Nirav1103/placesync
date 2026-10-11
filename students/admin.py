from django.contrib import admin
from .models import (
    Student, StudentSkill, StudentResume, Project,
    TechnicalLinks, Activity, WeeklySummary, MonthlySummary, ProjectMilestone,
    HackathonJournal, CodingPractice, LearningJournal, OpenSourceContribution,
    LearningGoal, DeveloperAchievement, Certificate, SemesterPerformance
)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display  = ('name', 'roll_number', 'department', 'batch', 'cgpa', 'placement_status')
    list_filter   = ('placement_status', 'department', 'batch')
    search_fields = ('name', 'roll_number', 'email')
    readonly_fields = ('resume_uploaded_at',)


@admin.register(StudentSkill)
class StudentSkillAdmin(admin.ModelAdmin):
    list_display  = ('name', 'category', 'proficiency', 'student')
    list_filter   = ('category', 'proficiency')
    search_fields = ('name', 'student__name', 'student__roll_number')
    autocomplete_fields = ('student',)


@admin.register(StudentResume)
class StudentResumeAdmin(admin.ModelAdmin):
    list_display  = ('student', 'resume_type', 'version', 'is_active', 'uploaded_at', 'ats_score')
    list_filter   = ('resume_type', 'is_active')
    search_fields = ('student__name', 'student__roll_number')
    autocomplete_fields = ('student',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'category', 'project_type', 'status', 'is_featured', 'created_at')
    list_filter = ('category', 'project_type', 'status', 'is_featured')
    search_fields = ('title', 'student__name', 'student__roll_number', 'technologies')
    autocomplete_fields = ('student',)


@admin.register(TechnicalLinks)
class TechnicalLinksAdmin(admin.ModelAdmin):
    list_display = ('student', 'github', 'leetcode', 'linkedin')
    search_fields = ('student__name', 'student__roll_number')


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'activity_type', 'category', 'date', 'hours_spent', 'status')
    list_filter = ('activity_type', 'category', 'status', 'date')
    search_fields = ('title', 'student__name', 'student__roll_number', 'technology_tags')


@admin.register(WeeklySummary)
class WeeklySummaryAdmin(admin.ModelAdmin):
    list_display = ('student', 'week_number', 'hours', 'problems_solved', 'date')
    list_filter = ('date',)
    search_fields = ('student__name', 'student__roll_number')


@admin.register(MonthlySummary)
class MonthlySummaryAdmin(admin.ModelAdmin):
    list_display = ('student', 'month', 'date')
    list_filter = ('date',)
    search_fields = ('student__name', 'student__roll_number', 'month')


@admin.register(ProjectMilestone)
class ProjectMilestoneAdmin(admin.ModelAdmin):
    list_display = ('project', 'milestone', 'progress_pct', 'hours', 'status', 'date')
    list_filter = ('status', 'date')
    search_fields = ('milestone', 'project__title', 'project__student__name')


@admin.register(HackathonJournal)
class HackathonJournalAdmin(admin.ModelAdmin):
    list_display = ('hackathon_name', 'student', 'organizer', 'date', 'theme', 'achievement')
    list_filter = ('date',)
    search_fields = ('hackathon_name', 'student__name', 'student__roll_number', 'project')


@admin.register(CodingPractice)
class CodingPracticeAdmin(admin.ModelAdmin):
    list_display = ('platform', 'student', 'problems_solved', 'difficulty', 'date')
    list_filter = ('platform', 'date')
    search_fields = ('student__name', 'student__roll_number')


@admin.register(LearningJournal)
class LearningJournalAdmin(admin.ModelAdmin):
    list_display = ('course', 'student', 'platform', 'progress', 'date')
    list_filter = ('platform', 'date')
    search_fields = ('course', 'student__name', 'student__roll_number')


@admin.register(OpenSourceContribution)
class OpenSourceContributionAdmin(admin.ModelAdmin):
    list_display = ('repository', 'student', 'date')
    list_filter = ('date',)
    search_fields = ('repository', 'student__name', 'student__roll_number')


@admin.register(LearningGoal)
class LearningGoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'priority', 'target_date', 'status')
    list_filter = ('priority', 'status', 'target_date')
    search_fields = ('title', 'student__name', 'student__roll_number')


@admin.register(DeveloperAchievement)
class DeveloperAchievementAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'category', 'date')
    list_filter = ('category', 'date')
    search_fields = ('title', 'student__name', 'student__roll_number')


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'issuing_organization', 'purpose', 'issue_date')
    list_filter = ('purpose', 'issue_date')
    search_fields = ('title', 'student__name', 'issuing_organization')


@admin.register(SemesterPerformance)
class SemesterPerformanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'semester', 'spi', 'status')
    list_filter = ('semester', 'status')
    search_fields = ('student__name', 'student__roll_number')
