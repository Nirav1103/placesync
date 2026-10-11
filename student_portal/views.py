from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
import datetime
from django.views import View
from django.http import FileResponse, HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Sum

from students.models import (
    Student, StudentSkill, StudentResume, Project,
    TechnicalLinks, Activity, WeeklySummary, MonthlySummary, ProjectMilestone,
    HackathonJournal, CodingPractice, LearningJournal, OpenSourceContribution,
    LearningGoal, DeveloperAchievement, Certificate
)
from placements.models import PlacementDrive, Application, DriveBookmark, PlacementCalendarEvent
from communication.models import Notification
from opportunities.models import ScrapedOpportunity
from .forms import (
    StudentSkillForm, ResumeUploadForm, ProjectForm,
    TechnicalLinksForm, ActivityForm, WeeklySummaryForm, MonthlySummaryForm, ProjectMilestoneForm,
    HackathonJournalForm, CodingPracticeForm, LearningJournalForm, OpenSourceContributionForm,
    LearningGoalForm, DeveloperAchievementForm, CertificateForm, PersonalProfileForm, AcademicProfileForm,
    CareerProfileForm
)
from .resume_analyzer import extract_pdf_text, analyze_resume_text
import json


# ─────────────────────────────────────────────────────────────────────────────
# Mixin: enforce student login + role guard
# ─────────────────────────────────────────────────────────────────────────────

class StudentRequiredMixin(LoginRequiredMixin):
    """Redirect to student login if user is not a STUDENT."""
    login_url = 'accounts:student_login'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role != 'STUDENT':
            # Admin trying to access student portal → send to admin dashboard
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)


def _get_student(request):
    """Helper: fetch Student profile for the current user."""
    try:
        return request.user.student_profile
    except Student.DoesNotExist:
        return None


def _base_ctx(request, student=None):
    """Common context keys needed by student_portal/base.html (sidebar badge etc.)"""
    unread = 0
    if request.user.is_authenticated:
        unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return {
        'student': student or _get_student(request),
        'unread_count': unread,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────────────────────────────────────

class StudentDashboardView(StudentRequiredMixin, View):
    template_name = 'student_portal/dashboard.html'

    def get(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            messages.error(request, "No student profile linked to your account.")
            return redirect('accounts:logout')

        applications = Application.objects.filter(student=student)
        app_count = applications.count()
        interview_count = applications.filter(
            status__in=['SHORTLISTED', 'SELECTED']
        ).count()
        offer_count = applications.filter(status='SELECTED').count()

        notif_count = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
        recent_notifs = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]

        # Open drives eligible for this student
        open_drives = PlacementDrive.objects.filter(
            college=student.college,
            status__in=['UPCOMING', 'ACTIVE'],
            eligible_departments=student.department,
        ).exclude(
            applications__student=student
        ).filter(
            min_cgpa__lte=student.cgpa or 0,
            max_backlogs__gte=student.backlogs,
        )[:5]

        # Upcoming deadlines (drives with deadlines in the future)
        upcoming_deadlines = PlacementDrive.objects.filter(
            college=student.college,
            status__in=['UPCOMING', 'ACTIVE'],
            deadline__isnull=False,
            deadline__gte=timezone.now().date(),
        ).order_by('deadline')[:5]

        recent_applications = applications.select_related(
            'drive', 'drive__company'
        ).order_by('-applied_at')[:5]

        # Compute scores
        profile_pct = student.profile_completion()
        ats = student.ats_score()
        readiness = student.placement_readiness()
        career = student.career_score()

        context = {
            **_base_ctx(request, student),
            'app_count': app_count,
            'interview_count': interview_count,
            'offer_count': offer_count,
            'notif_count': notif_count,
            'recent_notifs': recent_notifs,
            'open_drives': open_drives,
            'upcoming_deadlines': upcoming_deadlines,
            'recent_applications': recent_applications,
            'profile_pct': profile_pct,
            'ats_score': ats,
            'readiness_score': readiness,
            'career_score': career,
            'resume_uploaded': bool(student.resume),
        }
        return render(request, self.template_name, context)


# ─────────────────────────────────────────────────────────────────────────────
# Profile: View
# ─────────────────────────────────────────────────────────────────────────────

class StudentProfileView(StudentRequiredMixin, View):
    template_name = 'student_portal/profile.html'

    def get(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')
        return render(request, self.template_name, {
            **_base_ctx(request, student),
        })


# ─────────────────────────────────────────────────────────────────────────────
# Profile: Edit
# ─────────────────────────────────────────────────────────────────────────────

class StudentProfileEditView(StudentRequiredMixin, View):
    template_name = 'student_portal/profile_edit.html'

    def get(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')
        form = PersonalProfileForm(instance=student)
        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'form': form,
        })

    def post(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')
        form = PersonalProfileForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "Personal profile updated successfully.")
            return redirect('student_portal:profile')
        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'form': form,
        })


class StudentAcademicProfileView(StudentRequiredMixin, View):
    template_name = 'student_portal/academic_profile.html'

    def get(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        is_edit = (request.GET.get('edit') == '1')
        form = None
        if is_edit:
            form = AcademicProfileForm(instance=student)

        # Academic Performance List
        performances = list(student.semester_performances.all())
        if not performances:
            for sem in range(1, 9):
                if sem < student.semester:
                    status_val = "Completed"
                elif sem == student.semester:
                    status_val = "Current"
                else:
                    status_val = "Upcoming"
                
                performances.append({
                    'semester': sem,
                    'spi': None,
                    'status': status_val,
                })
        else:
            # Ensure semesters up to 8 are present in display list
            sem_map = {p.semester: p for p in performances}
            performances = []
            for sem in range(1, 9):
                if sem in sem_map:
                    performances.append(sem_map[sem])
                else:
                    if sem < student.semester:
                        status_val = "Completed"
                    elif sem == student.semester:
                        status_val = "Current"
                    else:
                        status_val = "Upcoming"
                    performances.append({
                        'semester': sem,
                        'spi': None,
                        'status': status_val,
                    })

        # Eligibility calculation
        min_required_cgpa = 6.00
        current_cgpa = float(student.cgpa or 0)
        is_eligible = (current_cgpa >= min_required_cgpa) and (student.backlogs == 0)

        # Academic Status description
        academic_status = "Not Eligible"
        if is_eligible:
            academic_status = "Eligible"

        # Calculate Completed Semesters count
        # A semester is completed if it is less than current semester and has an SPI set
        completed_count = student.semester_performances.filter(semester__lt=student.semester, spi__isnull=False).count()

        # Current Year text based on semester
        current_year_str = "1st Year"
        if student.semester in [3, 4]:
            current_year_str = "2nd Year"
        elif student.semester in [5, 6]:
            current_year_str = "3rd Year"
        elif student.semester in [7, 8]:
            current_year_str = "4th Year"

        context = {
            **_base_ctx(request, student),
            'performances': performances,
            'min_required_cgpa': min_required_cgpa,
            'is_eligible': is_eligible,
            'academic_status': academic_status,
            'completed_count': completed_count,
            'current_year_str': current_year_str,
            'is_edit': is_edit,
            'form': form,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')
        
        form = AcademicProfileForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "Academic profile updated successfully.")
            return redirect('student_portal:academic_profile')
        
        # If invalid, render form with errors
        # Academic Performance List
        performances = list(student.semester_performances.all())
        sem_map = {p.semester: p for p in performances}
        performances = []
        for sem in range(1, 9):
            if sem in sem_map:
                performances.append(sem_map[sem])
            else:
                if sem < student.semester:
                    status_val = "Completed"
                elif sem == student.semester:
                    status_val = "Current"
                else:
                    status_val = "Upcoming"
                performances.append({
                    'semester': sem,
                    'spi': None,
                    'status': status_val,
                })

        min_required_cgpa = 6.00
        current_cgpa = float(student.cgpa or 0)
        is_eligible = (current_cgpa >= min_required_cgpa) and (student.backlogs == 0)
        academic_status = "Not Eligible"
        if is_eligible:
            academic_status = "Eligible"

        completed_count = student.semester_performances.filter(semester__lt=student.semester, spi__isnull=False).count()
        current_year_str = "1st Year"
        if student.semester in [3, 4]:
            current_year_str = "2nd Year"
        elif student.semester in [5, 6]:
            current_year_str = "3rd Year"
        elif student.semester in [7, 8]:
            current_year_str = "4th Year"

        context = {
            **_base_ctx(request, student),
            'performances': performances,
            'min_required_cgpa': min_required_cgpa,
            'is_eligible': is_eligible,
            'academic_status': academic_status,
            'completed_count': completed_count,
            'current_year_str': current_year_str,
            'is_edit': True,
            'form': form,
        }
        return render(request, self.template_name, context)


# ─────────────────────────────────────────────────────────────────────────────
# Resume Upload
# ─────────────────────────────────────────────────────────────────────────────

class StudentResumeUploadView(StudentRequiredMixin, View):
    """Uploads a PDF resume/CV, stores file_size & resume_name, and extracts ATS metadata."""

    def post(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        form = ResumeUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, err)
            return redirect('student_portal:resume_dashboard')

        resume_name = form.cleaned_data.get('resume_name', '').strip()
        resume_type = form.cleaned_data['resume_type']
        is_default = form.cleaned_data.get('is_default', False)
        file = form.cleaned_data['file']

        if not resume_name:
            import os
            base_name, _ = os.path.splitext(file.name)
            resume_name = base_name.replace('_', ' ').replace('-', ' ').title()

        latest = StudentResume.objects.filter(student=student, resume_type=resume_type).order_by('-version').first()
        version = (latest.version + 1) if latest else 1

        new_resume = StudentResume(
            student=student,
            resume_name=resume_name,
            file=file,
            file_size=file.size,
            resume_type=resume_type,
            version=version,
            is_active=True
        )
        new_resume.save()

        # If first resume or requested, set as default
        has_existing_default = StudentResume.objects.filter(student=student, is_default=True).exists()
        if is_default or not has_existing_default:
            new_resume.set_as_default()

        # Execute text extraction & ATS analysis
        try:
            raw_text = extract_pdf_text(new_resume.file.path)
            analysis = analyze_resume_text(raw_text)

            new_resume.extracted_text = raw_text
            new_resume.ats_score = analysis['ats_score']
            new_resume.completion_score = analysis['completion_score']
            new_resume.formatting_score = analysis['formatting_score']
            new_resume.projects_found = json.dumps(analysis['projects_found'])
            new_resume.education_found = json.dumps(analysis['education_found'])
            new_resume.skills_found = json.dumps(analysis['skills_found'])
            new_resume.certificates_found = json.dumps(analysis['certificates_found'])
            new_resume.experience_found = json.dumps(analysis['experience_found'])
            new_resume.missing_keywords = json.dumps(analysis['missing_keywords'])
            new_resume.suggestions = json.dumps(analysis['suggestions'])
            new_resume.save()
        except Exception as e:
            messages.warning(request, f"Resume saved, but PDF text extraction failed: {e}")

        messages.success(request, f"Resume '{new_resume.display_name}' uploaded successfully!")
        return redirect('student_portal:resume_dashboard')


# ─────────────────────────────────────────────────────────────────────────────
# Placement Drives (Active, Upcoming, Closed, Bookmarks, Search, Filters)
# ─────────────────────────────────────────────────────────────────────────────

class StudentDrivesView(StudentRequiredMixin, View):
    template_name = 'student_portal/drives.html'

    def get(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        tab = request.GET.get('tab', 'active').strip().lower()
        q = request.GET.get('q', '').strip()
        drive_type = request.GET.get('type', '').strip()

        # Base filter by college and created by college admin
        drives = PlacementDrive.objects.filter(college=student.college)

        # Tab filters
        if tab == 'upcoming':
            drives = drives.filter(status='UPCOMING')
        elif tab == 'closed':
            drives = drives.filter(status='COMPLETED')
        else:
            tab = 'active'
            drives = drives.filter(status='ACTIVE')

        # Search filter
        if q:
            drives = drives.filter(
                Q(role__icontains=q) | 
                Q(company__name__icontains=q) |
                Q(company__industry__icontains=q)
            )

        # Type filter
        if drive_type:
            drives = drives.filter(drive_type=drive_type)

        drives = drives.select_related('company').order_by('deadline')

        # Retrieve student's applications and bookmarks
        applied_drive_ids = set(
            Application.objects.filter(student=student).values_list('drive_id', flat=True)
        )
        bookmarked_drive_ids = set(
            DriveBookmark.objects.filter(student=student).values_list('drive_id', flat=True)
        )

        drives_data = []
        for d in drives:
            # Auto-calculate basic eligibility check
            eligible = True
            
            # CGPA check
            if student.cgpa is not None and student.cgpa < d.min_cgpa:
                eligible = False
            # Department check
            if d.eligible_departments.exists() and student.department not in d.eligible_departments.all():
                eligible = False
            # Batch check
            if d.eligible_batches.exists() and student.batch not in d.eligible_batches.all():
                eligible = False
            # Backlog check
            if student.backlogs > d.max_backlogs:
                eligible = False
            # Skill check (if specified)
            if d.required_skills:
                req_skills = [s.strip().lower() for s in d.required_skills.split(',') if s.strip()]
                student_skills = [s.name.lower() for s in student.skill_entries.all()] + [s.strip().lower() for s in student.skills.split(',') if s.strip()]
                if any(rs not in student_skills for rs in req_skills):
                    eligible = False

            drives_data.append({
                'drive': d,
                'eligible': eligible,
                'applied': d.pk in applied_drive_ids,
                'bookmarked': d.pk in bookmarked_drive_ids,
            })

        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'drives_data': drives_data,
            'tab': tab,
            'q': q,
            'drive_type': drive_type,
            'applied_count': len(applied_drive_ids),
            'bookmark_count': len(bookmarked_drive_ids),
        })


class StudentDriveDetailView(StudentRequiredMixin, View):
    """Detailed view for a Placement Drive, checking eligibility criteria automatically."""
    template_name = 'student_portal/drive_detail.html'

    def get(self, request, pk, *args, **kwargs):
        student = _get_student(request)
        drive = get_object_or_404(PlacementDrive, pk=pk, college=student.college)

        # Eligibility checklist
        checklist = {
            'cgpa': {'name': 'CGPA Requirement', 'status': True, 'desc': f'Your CGPA: {student.cgpa or "N/A"} (Required: Min {drive.min_cgpa})'},
            'department': {'name': 'Department Eligibility', 'status': True, 'desc': f'Your Department: {student.department.name} (Eligible)'},
            'batch': {'name': 'Passing Batch', 'status': True, 'desc': f'Your Batch: {student.batch.name} (Eligible)'},
            'backlogs': {'name': 'Backlogs Limit', 'status': True, 'desc': f'Your Backlogs: {student.backlogs} (Allowed: Max {drive.max_backlogs})'},
            'skills': {'name': 'Required Skills', 'status': True, 'desc': 'All required skills matched'},
        }

        # 1. CGPA Check
        if student.cgpa is not None and student.cgpa < drive.min_cgpa:
            checklist['cgpa']['status'] = False
            checklist['cgpa']['desc'] = f'Your CGPA is {student.cgpa}, but a minimum of {drive.min_cgpa} is required.'
        elif student.cgpa is None:
            checklist['cgpa']['status'] = False
            checklist['cgpa']['desc'] = f'CGPA not defined on your profile. Required: Min {drive.min_cgpa}.'

        # 2. Department Check
        if drive.eligible_departments.exists() and student.department not in drive.eligible_departments.all():
            checklist['department']['status'] = False
            depts = ', '.join([d.code for d in drive.eligible_departments.all()])
            checklist['department']['desc'] = f'Eligible departments: {depts}. Your department is {student.department.code}.'

        # 3. Batch Check
        if drive.eligible_batches.exists() and student.batch not in drive.eligible_batches.all():
            checklist['batch']['status'] = False
            batches = ', '.join([b.name for b in drive.eligible_batches.all()])
            checklist['batch']['desc'] = f'Eligible batches: {batches}. Your batch is {student.batch.name}.'

        # 4. Backlogs Check
        if student.backlogs > drive.max_backlogs:
            checklist['backlogs']['status'] = False
            checklist['backlogs']['desc'] = f'You have {student.backlogs} active backlog(s). Maximum allowed: {drive.max_backlogs}.'

        # 5. Skills Check
        missing_skills = []
        if drive.required_skills:
            req_skills = [s.strip() for s in drive.required_skills.split(',') if s.strip()]
            student_skills = [s.name.lower() for s in student.skill_entries.all()] + [s.strip().lower() for s in student.skills.split(',') if s.strip()]
            for rs in req_skills:
                if rs.lower() not in student_skills:
                    missing_skills.append(rs)

            if missing_skills:
                checklist['skills']['status'] = False
                checklist['skills']['desc'] = f'Missing required skills: {", ".join(missing_skills)}.'

        # Decide overall eligibility
        is_eligible = all(item['status'] for item in checklist.values())

        # Check applied status
        application = Application.objects.filter(drive=drive, student=student).first()
        is_bookmarked = DriveBookmark.objects.filter(student=student, drive=drive).exists()

        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'drive': drive,
            'checklist': checklist,
            'is_eligible': is_eligible,
            'application': application,
            'is_bookmarked': is_bookmarked,
        })


class StudentBookmarkToggleView(StudentRequiredMixin, View):
    """POST-only view to toggle bookmark for a placement drive."""
    def post(self, request, pk, *args, **kwargs):
        student = _get_student(request)
        drive = get_object_or_404(PlacementDrive, pk=pk, college=student.college)
        
        bookmark = DriveBookmark.objects.filter(student=student, drive=drive).first()
        if bookmark:
            bookmark.delete()
            messages.success(request, f"Removed bookmark for {drive.role} at {drive.company.name}.")
        else:
            DriveBookmark.objects.create(student=student, drive=drive)
            messages.success(request, f"Bookmarked {drive.role} at {drive.company.name}!")
            
        return redirect(request.META.get('HTTP_REFERER', 'student_portal:drives'))


class StudentApplyView(StudentRequiredMixin, View):
    """POST endpoint to apply for a placement drive, verifying eligibility and populating calendar."""
    def post(self, request, pk, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        drive = get_object_or_404(PlacementDrive, pk=pk, college=student.college, status__in=['UPCOMING', 'ACTIVE'])

        # Check already applied
        if Application.objects.filter(drive=drive, student=student).exists():
            messages.warning(request, f"You have already applied to {drive.role} at {drive.company.name}.")
            return redirect('student_portal:drives')

        # Full eligibility criteria checks
        eligible = True
        
        if student.cgpa is not None and student.cgpa < drive.min_cgpa:
            eligible = False
        if drive.eligible_departments.exists() and student.department not in drive.eligible_departments.all():
            eligible = False
        if drive.eligible_batches.exists() and student.batch not in drive.eligible_batches.all():
            eligible = False
        if student.backlogs > drive.max_backlogs:
            eligible = False
        if drive.required_skills:
            req_skills = [s.strip().lower() for s in drive.required_skills.split(',') if s.strip()]
            student_skills = [s.name.lower() for s in student.skill_entries.all()] + [s.strip().lower() for s in student.skills.split(',') if s.strip()]
            if any(rs not in student_skills for rs in req_skills):
                eligible = False

        if not eligible:
            messages.error(request, "You do not meet the eligibility criteria for this drive.")
            return redirect('student_portal:drives')

        # Create application
        Application.objects.create(drive=drive, student=student, status='APPLIED')

        # Automatically populate Student Placement Calendar Events (6 specific types)
        today = timezone.localdate()
        
        # 1. Application Deadline
        deadline_date = drive.deadline if drive.deadline else (today + timezone.timedelta(days=4))
        PlacementCalendarEvent.objects.get_or_create(
            student=student,
            drive=drive,
            event_type='DEADLINE',
            defaults={
                'title': f"Application Deadline: {drive.company.name}",
                'description': f"Final date to submit applications for {drive.role}.",
                'event_date': deadline_date
            }
        )

        # 2. Aptitude Test
        PlacementCalendarEvent.objects.get_or_create(
            student=student,
            drive=drive,
            event_type='APTITUDE_TEST',
            defaults={
                'title': f"Aptitude Test: {drive.company.name}",
                'description': f"Structured numerical and logical testing round for {drive.role}.",
                'event_date': today + timezone.timedelta(days=2)
            }
        )

        # 3. Technical Interview
        PlacementCalendarEvent.objects.get_or_create(
            student=student,
            drive=drive,
            event_type='TECH_INTERVIEW',
            defaults={
                'title': f"Technical Interview: {drive.company.name}",
                'description': f"Technical rounds covering core concepts, DSA, and coding for {drive.role}.",
                'event_date': today + timezone.timedelta(days=5)
            }
        )

        # 4. HR Interview
        PlacementCalendarEvent.objects.get_or_create(
            student=student,
            drive=drive,
            event_type='HR_INTERVIEW',
            defaults={
                'title': f"HR Interview: {drive.company.name}",
                'description': f"Culture-fit, behavioral, and HR panel review for {drive.role}.",
                'event_date': today + timezone.timedelta(days=7)
            }
        )

        # 5. Offer Release
        PlacementCalendarEvent.objects.get_or_create(
            student=student,
            drive=drive,
            event_type='OFFER_RELEASE',
            defaults={
                'title': f"Offer Release: {drive.company.name}",
                'description': f"Declaration of selected candidates and offer letter release for {drive.role}.",
                'event_date': today + timezone.timedelta(days=9)
            }
        )

        # 6. Joining Date
        PlacementCalendarEvent.objects.get_or_create(
            student=student,
            drive=drive,
            event_type='JOINING_DATE',
            defaults={
                'title': f"Joining Date: {drive.company.name}",
                'description': f"Expected date of joining for the {drive.role} role.",
                'event_date': today + timezone.timedelta(days=30)
            }
        )

        messages.success(request, f"Successfully applied to {drive.role} at {drive.company.name}! Placement calendar updated.")
        return redirect('student_portal:applications')


# ─────────────────────────────────────────────────────────────────────────────
# Placement Calendar
# ─────────────────────────────────────────────────────────────────────────────

class StudentCalendarView(StudentRequiredMixin, View):
    """Displays placement drive timeline events for applied drives grouped by timeframe."""
    template_name = 'student_portal/calendar.html'

    def get(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        # Retrieve the drive IDs the student has applied for
        applied_drive_ids = Application.objects.filter(student=student).values_list('drive_id', flat=True)

        # Filter events by applied drives ONLY
        events = PlacementCalendarEvent.objects.filter(
            student=student,
            drive_id__in=applied_drive_ids
        ).select_related('drive', 'drive__company').order_by('event_date')

        # Timeframe groupings based on current date
        today = timezone.localdate()
        tomorrow = today + timezone.timedelta(days=1)
        end_of_week = today + timezone.timedelta(days=7)

        today_events = events.filter(event_date=today)
        tomorrow_events = events.filter(event_date=tomorrow)
        this_week_events = events.filter(event_date__gt=tomorrow, event_date__lte=end_of_week)
        upcoming_events = events.filter(event_date__gt=end_of_week)

        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'today_events': today_events,
            'tomorrow_events': tomorrow_events,
            'this_week_events': this_week_events,
            'upcoming_events': upcoming_events,
            'total_events': events.count(),
        })



# ─────────────────────────────────────────────────────────────────────────────
# Applications
# ─────────────────────────────────────────────────────────────────────────────

class StudentApplicationsView(StudentRequiredMixin, View):
    template_name = 'student_portal/applications.html'

    def get(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        applications = Application.objects.filter(
            student=student
        ).select_related('drive', 'drive__company').order_by('-applied_at')

        status_filter = request.GET.get('status', '')
        if status_filter:
            applications = applications.filter(status=status_filter)

        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'applications': applications,
            'status_filter': status_filter,
        })


# ─────────────────────────────────────────────────────────────────────────────
# Notifications
# ─────────────────────────────────────────────────────────────────────────────

class StudentNotificationsView(StudentRequiredMixin, View):
    template_name = 'student_portal/notifications.html'

    def get(self, request, *args, **kwargs):
        student = _get_student(request)
        notifications = Notification.objects.filter(user=request.user)
        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'notifications': notifications,
            'unread_count': notifications.filter(is_read=False).count(),
        })


class StudentMarkNotificationReadView(StudentRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        notif = get_object_or_404(Notification, pk=pk, user=request.user)
        notif.is_read = True
        notif.save()
        return redirect('student_portal:notifications')


# ─────────────────────────────────────────────────────────────────────────────
# Settings
# ─────────────────────────────────────────────────────────────────────────────

class StudentSettingsView(StudentRequiredMixin, View):
    template_name = 'student_portal/settings.html'

    def get(self, request, *args, **kwargs):
        student = _get_student(request)
        return render(request, self.template_name, {**_base_ctx(request, student)})


# ─────────────────────────────────────────────────────────────────────────────
# Skills — List / Add / Edit / Delete
# ─────────────────────────────────────────────────────────────────────────────

class StudentSkillsView(StudentRequiredMixin, View):
    """Display all skills grouped by category, with summary stats."""
    template_name = 'student_portal/skills.html'

    def get(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        all_skills = StudentSkill.objects.filter(student=student)

        # Group by category for section rendering
        categories = StudentSkill.Category.choices  # [(value, label), ...]
        grouped = {}
        for cat_value, cat_label in categories:
            skills_in_cat = all_skills.filter(category=cat_value)
            if skills_in_cat.exists():
                grouped[cat_value] = {
                    'label': cat_label,
                    'skills': skills_in_cat,
                    'icon': StudentSkill(category=cat_value).category_icon,
                }

        # Summary counts by proficiency
        beginner_count     = all_skills.filter(proficiency='BEGINNER').count()
        intermediate_count = all_skills.filter(proficiency='INTERMEDIATE').count()
        advanced_count     = all_skills.filter(proficiency='ADVANCED').count()

        # Category distribution for stat pills
        category_stats = []
        for cat_value, cat_label in categories:
            cnt = all_skills.filter(category=cat_value).count()
            if cnt:
                category_stats.append({'label': cat_label, 'count': cnt})

        form = StudentSkillForm()

        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'all_skills':        all_skills,
            'grouped':           grouped,
            'total_skills':      all_skills.count(),
            'beginner_count':    beginner_count,
            'intermediate_count':intermediate_count,
            'advanced_count':    advanced_count,
            'category_stats':    category_stats,
            'form':              form,
            'categories':        StudentSkill.Category.choices,
            'proficiencies':     StudentSkill.Proficiency.choices,
        })


class StudentSkillAddView(StudentRequiredMixin, View):
    """POST-only: add a new skill for the logged-in student."""

    def post(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        form = StudentSkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.student = student
            try:
                skill.save()
                messages.success(request, f'Skill "{skill.name}" added successfully!')
            except Exception:
                messages.error(request, f'Skill "{skill.name}" already exists in your list.')
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, err)

        return redirect('student_portal:skills')


class StudentSkillEditView(StudentRequiredMixin, View):
    """GET shows pre-filled edit form; POST saves changes."""
    template_name = 'student_portal/skill_edit.html'

    def _get_skill(self, request, pk):
        student = _get_student(request)
        return get_object_or_404(StudentSkill, pk=pk, student=student)

    def get(self, request, pk, *args, **kwargs):
        skill   = self._get_skill(request, pk)
        student = skill.student
        form    = StudentSkillForm(instance=skill)
        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'form':  form,
            'skill': skill,
        })

    def post(self, request, pk, *args, **kwargs):
        skill  = self._get_skill(request, pk)
        form   = StudentSkillForm(request.POST, instance=skill)
        if form.is_valid():
            form.save()
            messages.success(request, f'Skill "{skill.name}" updated.')
            return redirect('student_portal:skills')
        return render(request, self.template_name, {
            **_base_ctx(request, skill.student),
            'form':  form,
            'skill': skill,
        })


class StudentSkillDeleteView(StudentRequiredMixin, View):
    """POST-only: delete a skill (GET shows confirmation page)."""
    template_name = 'student_portal/skill_delete.html'

    def _get_skill(self, request, pk):
        student = _get_student(request)
        return get_object_or_404(StudentSkill, pk=pk, student=student)

    def get(self, request, pk, *args, **kwargs):
        skill   = self._get_skill(request, pk)
        return render(request, self.template_name, {
            **_base_ctx(request, skill.student),
            'skill': skill,
        })

    def post(self, request, pk, *args, **kwargs):
        skill = self._get_skill(request, pk)
        name  = skill.name
        skill.delete()
        messages.success(request, f'Skill "{name}" removed.')
        return redirect('student_portal:skills')


# ─────────────────────────────────────────────────────────────────────────────
# Resume & CV Dashboard views
# ─────────────────────────────────────────────────────────────────────────────

class StudentResumeDashboardView(StudentRequiredMixin, View):
    """Resume & CV Management page: list, search, filter, sort, upload form, pagination."""
    template_name = 'student_portal/resume_dashboard.html'

    def get(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        qs = StudentResume.objects.filter(student=student)

        # Search
        q = request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(resume_name__icontains=q) | Q(file__icontains=q))

        # Filter by type
        selected_type = request.GET.get('type', 'ALL').upper()
        if selected_type in ['RESUME', 'CV']:
            qs = qs.filter(resume_type=selected_type)

        # Sort by
        selected_sort = request.GET.get('sort', 'newest').lower()
        if selected_sort == 'oldest':
            qs = qs.order_by('uploaded_at')
        elif selected_sort == 'alphabetical':
            qs = qs.order_by('resume_name', 'file')
        else:
            qs = qs.order_by('-is_default', '-uploaded_at')

        all_student_resumes = StudentResume.objects.filter(student=student)
        total_count = all_student_resumes.count()
        resume_count = all_student_resumes.filter(resume_type='RESUME').count()
        cv_count = all_student_resumes.filter(resume_type='CV').count()
        default_resume = all_student_resumes.filter(is_default=True).first()

        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(qs, 6)  # 6 cards per page
        page_number = request.GET.get('page', 1)
        resumes_page = paginator.get_page(page_number)

        form = ResumeUploadForm()

        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'resumes': resumes_page,
            'paginator': paginator,
            'page_obj': resumes_page,
            'total_count': total_count,
            'total_resumes': total_count,
            'resume_count': resume_count,
            'resumes_count': resume_count,
            'cv_count': cv_count,
            'cvs_count': cv_count,
            'default_resume': default_resume,
            'q': q,
            'selected_type': selected_type,
            'selected_sort': selected_sort,
            'form': form,
            'max_file_size_mb': 5,
        })


class StudentResumeSetDefaultView(StudentRequiredMixin, View):
    """Marks selected resume as the Default Resume for the student."""
    def post(self, request, pk, *args, **kwargs):
        student = _get_student(request)
        resume = get_object_or_404(StudentResume, pk=pk, student=student)
        resume.set_as_default()
        messages.success(request, f"'{resume.display_name}' is now set as your default resume.")
        return redirect('student_portal:resume_dashboard')


class StudentResumeRenameView(StudentRequiredMixin, View):
    """Renames an existing uploaded resume."""
    def post(self, request, pk, *args, **kwargs):
        student = _get_student(request)
        resume = get_object_or_404(StudentResume, pk=pk, student=student)
        new_name = request.POST.get('resume_name', '').strip()
        if new_name:
            resume.resume_name = new_name
            resume.save()
            messages.success(request, "Resume renamed successfully.")
        else:
            messages.error(request, "Resume name cannot be empty.")
        return redirect('student_portal:resume_dashboard')


class StudentResumeDownloadView(StudentRequiredMixin, View):
    """Downloads resume PDF."""
    def get(self, request, pk, *args, **kwargs):
        student = _get_student(request)
        resume = get_object_or_404(StudentResume, pk=pk, student=student)
        response = FileResponse(resume.file.open('rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{resume.filename}"'
        return response


class StudentResumePreviewView(StudentRequiredMixin, View):
    """Streams PDF inline for browser viewing."""
    def get(self, request, pk, *args, **kwargs):
        student = _get_student(request)
        resume = get_object_or_404(StudentResume, pk=pk, student=student)
        response = FileResponse(resume.file.open('rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{resume.filename}"'
        return response


class StudentResumeDeleteView(StudentRequiredMixin, View):
    """GET shows delete confirmation, POST performs deletion and updates active status."""
    template_name = 'student_portal/resume_delete.html'

    def get(self, request, pk, *args, **kwargs):
        student = _get_student(request)
        resume = get_object_or_404(StudentResume, pk=pk, student=student)
        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'resume': resume
        })

    def post(self, request, pk, *args, **kwargs):
        student = _get_student(request)
        resume = get_object_or_404(StudentResume, pk=pk, student=student)
        display_name = resume.display_name
        was_default = resume.is_default

        try:
            resume.file.delete(save=False)
        except Exception:
            pass
        resume.delete()

        if was_default:
            next_resume = StudentResume.objects.filter(student=student).order_by('-uploaded_at').first()
            if next_resume:
                next_resume.set_as_default()
            else:
                student.resume = None
                student.save()

        messages.success(request, f"Resume '{display_name}' deleted successfully.")
        return redirect('student_portal:resume_dashboard')


class StudentATSAnalysisView(StudentRequiredMixin, View):
    """ATS Analysis Page: Select resume from dropdown, view detailed ATS score, strengths, weaknesses, missing skills & feedback."""
    template_name = 'student_portal/ats_analysis.html'

    def get(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        all_resumes = list(StudentResume.objects.filter(student=student).order_by('-is_default', '-uploaded_at'))
        
        selected_id = request.GET.get('resume_id')
        selected_resume = None
        if selected_id:
            try:
                selected_resume = StudentResume.objects.get(pk=selected_id, student=student)
            except StudentResume.DoesNotExist:
                selected_resume = None

        if not selected_resume and all_resumes:
            selected_resume = next((r for r in all_resumes if r.is_default), all_resumes[0])

        analysis_data = None
        if selected_resume:
            if not selected_resume.extracted_text and selected_resume.file:
                try:
                    raw_text = extract_pdf_text(selected_resume.file.path)
                    res_analysis = analyze_resume_text(raw_text)
                    selected_resume.extracted_text = raw_text
                    selected_resume.ats_score = res_analysis['ats_score']
                    selected_resume.completion_score = res_analysis['completion_score']
                    selected_resume.formatting_score = res_analysis['formatting_score']
                    selected_resume.projects_found = json.dumps(res_analysis['projects_found'])
                    selected_resume.education_found = json.dumps(res_analysis['education_found'])
                    selected_resume.skills_found = json.dumps(res_analysis['skills_found'])
                    selected_resume.certificates_found = json.dumps(res_analysis['certificates_found'])
                    selected_resume.experience_found = json.dumps(res_analysis['experience_found'])
                    selected_resume.missing_keywords = json.dumps(res_analysis['missing_keywords'])
                    selected_resume.suggestions = json.dumps(res_analysis['suggestions'])
                    selected_resume.save()
                except Exception:
                    pass

            projects = json.loads(selected_resume.projects_found or '[]')
            education = json.loads(selected_resume.education_found or '[]')
            skills = json.loads(selected_resume.skills_found or '[]')
            certificates = json.loads(selected_resume.certificates_found or '[]')
            experience = json.loads(selected_resume.experience_found or '[]')
            missing = json.loads(selected_resume.missing_keywords or '[]')
            suggestions = json.loads(selected_resume.suggestions or '[]')

            strengths = []
            if selected_resume.ats_score >= 80:
                strengths.append("High overall ATS Compatibility score")
            if len(skills) >= 5:
                strengths.append(f"Identified {len(skills)} relevant technical skills")
            if len(projects) >= 2:
                strengths.append(f"Found {len(projects)} technical projects")
            if len(education) >= 1:
                strengths.append("Clear education section detected")
            if len(experience) >= 1:
                strengths.append("Work/Internship experience highlighted")
            if selected_resume.formatting_score >= 80:
                strengths.append("Clean PDF formatting with standard section headers")
            if not strengths:
                strengths.append("Valid PDF format readable by ATS parsers")

            weaknesses = []
            if selected_resume.ats_score < 70:
                weaknesses.append("Overall ATS compatibility score is below target threshold (70%)")
            if len(skills) < 4:
                weaknesses.append("Low technical skills keyword density")
            if len(projects) < 2:
                weaknesses.append("Fewer than 2 technical projects detected")
            if len(experience) == 0:
                weaknesses.append("No explicit work or internship experience section found")
            if missing:
                weaknesses.append(f"Missing {len(missing)} key placement keywords ({', '.join(missing[:3])})")
            if not weaknesses:
                weaknesses.append("No critical section weaknesses detected")

            keyword_match_pct = max(10, min(100, int(selected_resume.ats_score * 0.95)))

            analysis_data = {
                'projects': projects,
                'education': education,
                'skills': skills,
                'certificates': certificates,
                'experience': experience,
                'missing_keywords': missing,
                'suggestions': suggestions,
                'strengths': strengths,
                'weaknesses': weaknesses,
                'keyword_match_pct': keyword_match_pct,
            }

        # Handle optional inline comparison parameters
        pk1 = request.GET.get('resume_a')
        pk2 = request.GET.get('resume_b')
        comp_ver1 = None
        comp_ver2 = None
        comp_analysis1 = None
        comp_analysis2 = None
        comp_recommendation = None

        if pk1 and pk2:
            comp_ver1 = StudentResume.objects.filter(pk=pk1, student=student).first()
            comp_ver2 = StudentResume.objects.filter(pk=pk2, student=student).first()

            if comp_ver1 and comp_ver2:
                p1 = json.loads(comp_ver1.projects_found or '[]')
                e1 = json.loads(comp_ver1.education_found or '[]')
                s1 = json.loads(comp_ver1.skills_found or '[]')
                ex1 = json.loads(comp_ver1.experience_found or '[]')
                m1 = json.loads(comp_ver1.missing_keywords or '[]')

                p2 = json.loads(comp_ver2.projects_found or '[]')
                e2 = json.loads(comp_ver2.education_found or '[]')
                s2 = json.loads(comp_ver2.skills_found or '[]')
                ex2 = json.loads(comp_ver2.experience_found or '[]')
                m2 = json.loads(comp_ver2.missing_keywords or '[]')

                comp_analysis1 = {
                    'projects': p1, 'education': e1, 'skills': s1, 'experience': ex1, 'keywords': m1,
                    'keyword_match': max(10, min(100, int(comp_ver1.ats_score * 0.95)))
                }
                comp_analysis2 = {
                    'projects': p2, 'education': e2, 'skills': s2, 'experience': ex2, 'keywords': m2,
                    'keyword_match': max(10, min(100, int(comp_ver2.ats_score * 0.95)))
                }

                if comp_ver1.ats_score > comp_ver2.ats_score:
                    rec_resume = comp_ver1
                    other_resume = comp_ver2
                    rec_key = 'A'
                elif comp_ver2.ats_score > comp_ver1.ats_score:
                    rec_resume = comp_ver2
                    other_resume = comp_ver1
                    rec_key = 'B'
                elif len(s1) >= len(s2):
                    rec_resume = comp_ver1
                    other_resume = comp_ver2
                    rec_key = 'A'
                else:
                    rec_resume = comp_ver2
                    other_resume = comp_ver1
                    rec_key = 'B'

                explanation = (
                    f"Resume {rec_key} ('{rec_resume.display_name}') is recommended because it achieved a higher ATS score "
                    f"({rec_resume.ats_score}/100 vs {other_resume.ats_score}/100) and contains better keyword optimization."
                )

                comp_recommendation = {
                    'winner_key': rec_key,
                    'winner': rec_resume,
                    'explanation': explanation,
                }

        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'all_resumes': all_resumes,
            'selected_resume': selected_resume,
            'analysis': analysis_data,
            'comp_ver1': comp_ver1,
            'comp_ver2': comp_ver2,
            'comp_analysis1': comp_analysis1,
            'comp_analysis2': comp_analysis2,
            'comp_recommendation': comp_recommendation,
        })


class StudentResumeCompareView(StudentRequiredMixin, View):
    """Allows side-by-side comparison of any two uploaded resumes."""
    template_name = 'student_portal/resume_compare.html'

    def get(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        all_resumes = StudentResume.objects.filter(student=student).order_by('-is_default', '-uploaded_at')

        pk1 = request.GET.get('version1') or request.GET.get('resume_a')
        pk2 = request.GET.get('version2') or request.GET.get('resume_b')

        if not pk1 or not pk2:
            if all_resumes.count() >= 2:
                pk1 = all_resumes[0].pk
                pk2 = all_resumes[1].pk

        ver1 = None
        ver2 = None
        analysis1 = None
        analysis2 = None
        recommendation = None

        if pk1 and pk2:
            ver1 = StudentResume.objects.filter(pk=pk1, student=student).first()
            ver2 = StudentResume.objects.filter(pk=pk2, student=student).first()

        if ver1 and ver2:
            p1 = json.loads(ver1.projects_found or '[]')
            e1 = json.loads(ver1.education_found or '[]')
            s1 = json.loads(ver1.skills_found or '[]')
            ex1 = json.loads(ver1.experience_found or '[]')
            m1 = json.loads(ver1.missing_keywords or '[]')

            p2 = json.loads(ver2.projects_found or '[]')
            e2 = json.loads(ver2.education_found or '[]')
            s2 = json.loads(ver2.skills_found or '[]')
            ex2 = json.loads(ver2.experience_found or '[]')
            m2 = json.loads(ver2.missing_keywords or '[]')

            analysis1 = {
                'projects': p1, 'education': e1, 'skills': s1, 'experience': ex1, 'keywords': m1,
                'keyword_match': max(10, min(100, int(ver1.ats_score * 0.95)))
            }
            analysis2 = {
                'projects': p2, 'education': e2, 'skills': s2, 'experience': ex2, 'keywords': m2,
                'keyword_match': max(10, min(100, int(ver2.ats_score * 0.95)))
            }

            if ver1.ats_score > ver2.ats_score:
                rec_resume = ver1
                other_resume = ver2
                rec_key = 'A'
            elif ver2.ats_score > ver1.ats_score:
                rec_resume = ver2
                other_resume = ver1
                rec_key = 'B'
            elif len(s1) >= len(s2):
                rec_resume = ver1
                other_resume = ver2
                rec_key = 'A'
            else:
                rec_resume = ver2
                other_resume = ver1
                rec_key = 'B'

            explanation = (
                f"Resume {rec_key} ('{rec_resume.display_name}') is recommended because it achieved a higher ATS score "
                f"({rec_resume.ats_score}/100 vs {other_resume.ats_score}/100) and contains better section formatting."
            )

            recommendation = {
                'winner_key': rec_key,
                'winner': rec_resume,
                'explanation': explanation,
            }

        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'all_resumes': all_resumes,
            'ver1': ver1,
            'ver2': ver2,
            'analysis1': analysis1,
            'analysis2': analysis2,
            'recommendation': recommendation,
        })


# ─────────────────────────────────────────────────────────────────────────────
# AI Career Intelligence View
# ─────────────────────────────────────────────────────────────────────────────

class StudentRecommendationsView(StudentRequiredMixin, View):
    """AI Career Intelligence dashboard: analyzes student's complete profile and placement readiness."""
    template_name = 'student_portal/recommendations.html'

    def get(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        # ── 1. Academic Data & Score ──────────────────────
        cgpa_val = float(student.cgpa or 0)
        backlogs_count = student.backlogs or 0
        academic_score = max(0, min(100, int((cgpa_val / 10.0) * 100) - (backlogs_count * 15)))
        if student.tenth_percentage and float(student.tenth_percentage) >= 75 and student.twelfth_percentage and float(student.twelfth_percentage) >= 75:
            academic_score = min(100, academic_score + 10)

        academic_status = 'Excellent' if academic_score >= 80 else 'Good' if academic_score >= 65 else 'Average' if academic_score >= 50 else 'Needs Improvement'

        # ── 2. Projects Data & Score ──────────────────────
        projects_qs = student.projects.all()
        projects_count = projects_qs.count()
        featured_projects = projects_qs.filter(is_featured=True).count()
        linked_projects = projects_qs.filter(Q(github_url__gt='') | Q(live_url__gt='')).count()

        if projects_count == 0:
            projects_score = 15
        elif projects_count == 1:
            projects_score = 50 + (10 if linked_projects > 0 else 0)
        elif projects_count == 2:
            projects_score = 70 + (10 if featured_projects > 0 else 0)
        else:
            projects_score = min(100, 85 + (projects_count * 3) + (10 if featured_projects > 0 else 0))

        projects_status = 'Excellent' if projects_score >= 80 else 'Good' if projects_score >= 65 else 'Average' if projects_score >= 50 else 'Needs Improvement'

        # ── 3. Skills Data & Score ────────────────────────
        skill_entries = list(student.skill_entries.all())
        raw_skills = [s.strip().lower() for s in (student.skills or '').split(',') if s.strip()]
        all_skills_set = set(raw_skills + [se.name.strip().lower() for se in skill_entries])

        # Active resume skills
        active_resume = student.resume_versions.filter(is_active=True).first()
        if active_resume and active_resume.skills_found:
            try:
                for s in json.loads(active_resume.skills_found or '[]'):
                    all_skills_set.add(s.strip().lower())
            except Exception:
                pass

        skills_count = len(all_skills_set)
        if skills_count == 0:
            skills_score = 10
        elif skills_count < 4:
            skills_score = 45
        elif skills_count < 8:
            skills_score = 70
        else:
            skills_score = min(100, 80 + (skills_count * 2))

        skills_status = 'Excellent' if skills_score >= 80 else 'Good' if skills_score >= 65 else 'Average' if skills_score >= 50 else 'Needs Improvement'

        # ── 4. Resume & ATS Score ─────────────────────────
        if active_resume:
            ats_val = active_resume.ats_score or 65
            resume_score = min(100, int(ats_val))
        elif student.resume:
            resume_score = 55
        else:
            resume_score = 25

        resume_status = 'Excellent' if resume_score >= 80 else 'Good' if resume_score >= 65 else 'Average' if resume_score >= 50 else 'Needs Improvement'

        # ── 5. Certificates Score ─────────────────────────
        certs_qs = student.certificates.all()
        certs_count = certs_qs.count()
        if certs_count == 0:
            certs_score = 20
        elif certs_count == 1:
            certs_score = 60
        elif certs_count == 2:
            certs_score = 80
        else:
            certs_score = min(100, 90 + (certs_count * 3))

        certs_status = 'Excellent' if certs_score >= 80 else 'Good' if certs_score >= 65 else 'Average' if certs_score >= 50 else 'Needs Improvement'

        # ── 6. Developer Journey Score ────────────────────
        journey_qs = student.journey_activities.all()
        activities_count = journey_qs.count()
        total_hours = sum([float(a.hours_spent or 0) for a in journey_qs])
        coding_practices_count = student.coding_practices.count()
        hackathons_count = student.hackathons.count()

        if activities_count == 0 and coding_practices_count == 0 and hackathons_count == 0:
            journey_score = 25
        else:
            base_j = min(60, activities_count * 10 + coding_practices_count * 15 + hackathons_count * 20)
            hours_bonus = min(40, int(total_hours * 2))
            journey_score = min(100, base_j + hours_bonus)

        journey_status = 'Excellent' if journey_score >= 80 else 'Good' if journey_score >= 65 else 'Average' if journey_score >= 50 else 'Needs Improvement'

        # ── 7. Profile Completion Score ───────────────────
        profile_comp_score = student.profile_completion()

        # ── OVERALL READINESS SCORE (Weighted Calculation) ─
        weighted_readiness = (
            (academic_score * 0.20) +
            (projects_score * 0.20) +
            (skills_score * 0.20) +
            (resume_score * 0.15) +
            (certs_score * 0.10) +
            (journey_score * 0.10) +
            (profile_comp_score * 0.05)
        )
        overall_readiness = round(weighted_readiness)

        if overall_readiness >= 80:
            overall_status = 'Excellent'
            overall_status_class = 'sp-badge-green'
            overall_color = '#10b981'
        elif overall_readiness >= 65:
            overall_status = 'Good'
            overall_status_class = 'sp-badge-sky'
            overall_color = '#0ea5e9'
        elif overall_readiness >= 50:
            overall_status = 'Average'
            overall_status_class = 'sp-badge-amber'
            overall_color = '#f59e0b'
        else:
            overall_status = 'Needs Improvement'
            overall_status_class = 'sp-badge-rose'
            overall_color = '#f43f5e'

        # Calculate stroke-dashoffset for circular SVG progress ring (radius=70, circumference=439.82)
        circle_offset = round(439.82 * (1.0 - (overall_readiness / 100.0)), 2)

        # ── SECTION 2: Profile Strength Cards ─────────────
        profile_strength_cards = [
            {'title': 'Academic', 'pct': academic_score, 'status': academic_status, 'icon': '🎓', 'color': '#0ea5e9'},
            {'title': 'Projects', 'pct': projects_score, 'status': projects_status, 'icon': '🔨', 'color': '#6366f1'},
            {'title': 'Skills', 'pct': skills_score, 'status': skills_status, 'icon': '💻', 'color': '#10b981'},
            {'title': 'Resume', 'pct': resume_score, 'status': resume_status, 'icon': '📄', 'color': '#ec4899'},
            {'title': 'Certificates', 'pct': certs_score, 'status': certs_status, 'icon': '🏆', 'color': '#f59e0b'},
            {'title': 'Developer Journey', 'pct': journey_score, 'status': journey_status, 'icon': '🚀', 'color': '#8b5cf6'},
        ]

        # ── SECTION 3: Strengths ──────────────────────────
        strengths = []
        if cgpa_val >= 7.5:
            strengths.append(f"Excellent Academic Performance (CGPA {cgpa_val:.2f} / 10.0)")
        elif cgpa_val >= 6.5:
            strengths.append(f"Good Academic Performance (CGPA {cgpa_val:.2f} / 10.0)")

        top_matched = [s.title() for s in ['python', 'django', 'java', 'javascript', 'react', 'sql', 'cpp', 'c++'] if s in all_skills_set]
        if top_matched:
            strengths.append(f"Strong {top_matched[0]} & Technical Skills ({', '.join(top_matched[:3])})")

        if projects_count >= 2:
            strengths.append(f"Good Project Portfolio ({projects_count} Active Projects)")
        elif projects_count == 1:
            strengths.append("Verified Practical Project Experience")

        if active_resume and active_resume.ats_score >= 70:
            strengths.append(f"Strong Resume (ATS Score: {active_resume.ats_score}/100)")
        elif student.resume:
            strengths.append("Active Resume Uploaded")

        if certs_count >= 1:
            strengths.append(f"Verified Credentials ({certs_count} Certificates)")

        if activities_count >= 2 or total_hours > 5:
            strengths.append("Active Learning Journey & Continuous Progress")

        if backlogs_count == 0:
            strengths.append("Clean Academic Record with Zero Backlogs")

        if len(strengths) < 2:
            strengths.append("Registered Active Student Account")

        # ── SECTION 4: Areas to Improve ───────────────────
        improvements = []
        if not any(s in all_skills_set for s in ['docker', 'aws', 'kubernetes', 'cloud', 'azure']):
            improvements.append("Add Cloud Skills (Learn Docker / AWS Basics)")
        if not active_resume or (active_resume and active_resume.ats_score < 80):
            improvements.append("Improve Resume Keywords to boost ATS Score above 85")
        if projects_count < 3:
            improvements.append("Build One More Full Stack Project")
        if certs_count < 2:
            improvements.append("Earn 1-2 Industry Certifications")
        if activities_count < 4:
            improvements.append("Log Daily Coding Practice & Milestones in Developer Journey")
        if not student.github_url or not student.linkedin_url:
            improvements.append("Add GitHub and LinkedIn URLs to Student Profile")
        if backlogs_count > 0:
            improvements.append(f"Clear Active Academic Backlogs ({backlogs_count} remaining)")

        if len(improvements) == 0:
            improvements.append("Maintain consistent coding practice and participate in mock interviews")

        # ── SECTION 5: Career Role Recommendation ─────────
        career_roles = []
        # Backend Developer
        backend_match_skills = [s for s in ['python', 'django', 'sql', 'postgresql', 'node', 'api', 'flask', 'express', 'mysql'] if s in all_skills_set]
        backend_pct = min(96, 50 + len(backend_match_skills) * 10 + (10 if projects_count >= 2 else 0))
        career_roles.append({
            'title': 'Backend Developer',
            'confidence': backend_pct,
            'matching_skills': [s.title() for s in backend_match_skills[:4]] or ['Python', 'SQL', 'REST API']
        })

        # Software Engineer
        swe_match_skills = [s for s in ['java', 'python', 'cpp', 'c++', 'data structures', 'algorithms', 'git', 'sql'] if s in all_skills_set]
        swe_pct = min(94, 55 + len(swe_match_skills) * 9 + (5 if cgpa_val >= 7.5 else 0))
        career_roles.append({
            'title': 'Software Engineer',
            'confidence': swe_pct,
            'matching_skills': [s.title() for s in swe_match_skills[:4]] or ['OOP', 'Algorithms', 'Git']
        })

        # Full Stack Developer
        fs_match_skills = [s for s in ['html', 'css', 'javascript', 'react', 'vue', 'django', 'node', 'express', 'tailwind'] if s in all_skills_set]
        fs_pct = min(92, 45 + len(fs_match_skills) * 9 + (15 if projects_count >= 2 else 0))
        career_roles.append({
            'title': 'Full Stack Developer',
            'confidence': fs_pct,
            'matching_skills': [s.title() for s in fs_match_skills[:4]] or ['JavaScript', 'React', 'HTML/CSS']
        })

        # Data Analyst
        data_match_skills = [s for s in ['python', 'pandas', 'numpy', 'sql', 'machine learning', 'data science', 'ai', 'tableau', 'powerbi'] if s in all_skills_set]
        data_pct = min(90, 40 + len(data_match_skills) * 12 + (10 if cgpa_val >= 8.0 else 0))
        career_roles.append({
            'title': 'Data Analyst',
            'confidence': data_pct,
            'matching_skills': [s.title() for s in data_match_skills[:4]] or ['Python', 'SQL', 'Data Analytics']
        })

        career_roles = sorted(career_roles, key=lambda x: x['confidence'], reverse=True)

        # ── SECTION 6: AI Career Roadmap ──────────────────
        roadmap = [
            {'week': 'Week 1', 'action': 'Learn Git & Version Control Basics'},
            {'week': 'Week 2', 'action': 'Complete Docker Basics & Containerization'},
            {'week': 'Week 3', 'action': 'Build REST API Project with Database Integration'},
            {'week': 'Week 4', 'action': 'Improve Resume & Optimize ATS Keywords'},
        ]

        # ── SECTION 7: Monthly Goals ──────────────────────
        monthly_goals = [
            {'title': 'Complete 2 Projects', 'completed': projects_count >= 2},
            {'title': 'Earn 1 Certificate', 'completed': certs_count >= 1},
            {'title': 'Increase ATS Score above 85', 'completed': (active_resume and active_resume.ats_score >= 85)},
            {'title': 'Participate in Hackathon', 'completed': hackathons_count > 0},
        ]

        # ── SECTION 8: Placement Readiness Timeline Graph ──
        timeline_trend = [
            {'label': 'ATS Score', 'score': resume_score},
            {'label': 'Projects', 'score': projects_score},
            {'label': 'Certificates', 'score': certs_score},
            {'label': 'Developer Journey', 'score': journey_score},
            {'label': 'Skills', 'score': skills_score},
        ]

        # ── EXPLANATION ("Why did I get this score?") ──────
        score_explanations = [
            {'category': 'Academic Performance', 'weight': '20%', 'score': academic_score, 'reason': f"CGPA: {cgpa_val:.2f}/10.0, Active Backlogs: {backlogs_count}."},
            {'category': 'Project Portfolio', 'weight': '20%', 'score': projects_score, 'reason': f"Total Projects: {projects_count}, Featured: {featured_projects}."},
            {'category': 'Technical Skills', 'weight': '20%', 'score': skills_score, 'reason': f"Identified Skills: {skills_count} total across profile/resume."},
            {'category': 'Resume Quality', 'weight': '15%', 'score': resume_score, 'reason': f"Active ATS Resume Score: {resume_score}/100."},
            {'category': 'Certificates', 'weight': '10%', 'score': certs_score, 'reason': f"Certificates Uploaded: {certs_count}."},
            {'category': 'Developer Journey', 'weight': '10%', 'score': journey_score, 'reason': f"Activities Logged: {activities_count}, Total Hours: {total_hours:.1f} hrs."},
            {'category': 'Profile Completion', 'weight': '5%', 'score': profile_comp_score, 'reason': f"Profile Completion: {profile_comp_score}%."},
        ]

        # ── ML AI ENGINE INTEGRATION ───────────────────────
        from analytics.ai_services import (
            predict_placement_readiness,
            predict_fresher_salary,
            recommend_career_roles,
            analyze_skill_gaps
        )

        ml_placement = predict_placement_readiness(student)
        predicted_salary_lpa = predict_fresher_salary(student)
        ml_career_roles = recommend_career_roles(student)
        ml_skill_gap = analyze_skill_gaps(student)

        overall_readiness = ml_placement['probability']
        overall_status = ml_placement['status']
        overall_status_class = ml_placement['badge_class']
        overall_color = '#10b981' if overall_readiness >= 80 else '#0ea5e9' if overall_readiness >= 65 else '#f59e0b' if overall_readiness >= 50 else '#f43f5e'
        circle_offset = round(439.82 * (1.0 - (overall_readiness / 100.0)), 2)

        # Career Intelligence Score (Master Composite 0-100)
        career_intel_score = round((overall_readiness * 0.40) + (resume_score * 0.20) + (profile_comp_score * 0.20) + (skills_score * 0.20))

        # ── 6 CHART.JS DATASETS PREPARATION ─────────────────
        # Chart 1: Placement Readiness Radar/Doughnut Data
        chart_readiness_labels = ['Academic', 'Projects', 'Skills', 'Resume ATS', 'Certificates', 'Developer Journey']
        chart_readiness_data = [academic_score, projects_score, skills_score, resume_score, certs_score, journey_score]

        # Chart 2: Skill Distribution Categorization
        prog_count = sum(1 for se in skill_entries if se.category == 'PROGRAMMING') or len([s for s in raw_skills if s in ['python', 'java', 'c++', 'javascript', 'html', 'css', 'sql']])
        fw_count = sum(1 for se in skill_entries if se.category in ['FRAMEWORK', 'DATABASE']) or len([s for s in raw_skills if s in ['django', 'react', 'node', 'express', 'postgresql', 'mongodb']])
        tools_count = sum(1 for se in skill_entries if se.category in ['TOOLS', 'CLOUD']) or len([s for s in raw_skills if s in ['git', 'docker', 'aws', 'linux', 'postman']])
        soft_count = sum(1 for se in skill_entries if se.category == 'SOFT_SKILLS') or 3

        chart_skills_labels = ['Programming Languages', 'Frameworks & DBs', 'Tools & Cloud', 'Soft Skills']
        chart_skills_data = [max(1, prog_count), max(1, fw_count), max(1, tools_count), max(1, soft_count)]

        # Chart 3: Top Technology Usage Frequency
        tech_freq = {}
        for p in projects_qs:
            for t in p.technology_list:
                tech_freq[t] = tech_freq.get(t, 0) + 1
        for s in raw_skills:
            s_name = s.title()
            tech_freq[s_name] = tech_freq.get(s_name, 0) + 1

        sorted_tech = sorted(tech_freq.items(), key=lambda x: x[1], reverse=True)[:6]
        if not sorted_tech:
            sorted_tech = [('Python', 3), ('Django', 2), ('JavaScript', 2), ('SQL', 1), ('Git', 1)]

        chart_tech_labels = [item[0] for item in sorted_tech]
        chart_tech_data = [item[1] for item in sorted_tech]

        # Chart 4: Salary Prediction Benchmarks
        chart_salary_labels = ['Fresher National Avg', 'Your ML Predicted CTC', 'Tier-1 Campus Avg', 'Top 10% Premium CTC']
        chart_salary_data = [4.5, predicted_salary_lpa, max(9.0, predicted_salary_lpa * 1.15), max(16.0, predicted_salary_lpa * 1.6)]

        # Chart 5: Career Growth Matrix (6 Months projection)
        chart_growth_labels = ['Month -3', 'Month -2', 'Month -1', 'Current', 'Target M+1', 'Target M+2']
        chart_growth_data = [
            max(20, overall_readiness - 30),
            max(25, overall_readiness - 20),
            max(30, overall_readiness - 10),
            overall_readiness,
            min(98, overall_readiness + 12),
            min(99, overall_readiness + 22)
        ]

        # Chart 6: Learning Progress & Activity Hours
        chart_learning_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        chart_learning_data = [2, 5, 8, 12, max(15, activities_count * 3), max(20, int(total_hours + 5))]

        # Industry Trending Skills List
        all_skill_names_lower = [s.lower() for s in all_skills_set]
        trending_skills = [
            {'name': 'Python', 'category': 'Backend / AI', 'demand': 95, 'acquired': 'python' in all_skill_names_lower},
            {'name': 'React.js', 'category': 'Frontend', 'demand': 92, 'acquired': 'react' in all_skill_names_lower or 'react.js' in all_skill_names_lower},
            {'name': 'Docker', 'category': 'DevOps / Cloud', 'demand': 88, 'acquired': 'docker' in all_skill_names_lower},
            {'name': 'AWS Cloud', 'category': 'Cloud Infrastructure', 'demand': 90, 'acquired': 'aws' in all_skill_names_lower or 'cloud' in all_skill_names_lower},
            {'name': 'PostgreSQL', 'category': 'Database Architecture', 'demand': 86, 'acquired': 'postgresql' in all_skill_names_lower or 'postgres' in all_skill_names_lower},
            {'name': 'REST API Design', 'category': 'Web Services', 'demand': 94, 'acquired': 'api' in all_skill_names_lower or 'django' in all_skill_names_lower},
            {'name': 'Git & GitHub', 'category': 'Version Control', 'demand': 98, 'acquired': 'git' in all_skill_names_lower or 'github' in all_skill_names_lower},
            {'name': 'Machine Learning', 'category': 'Data & AI', 'demand': 85, 'acquired': 'machine learning' in all_skill_names_lower or 'scikit-learn' in all_skill_names_lower},
        ]

        # Merge ML roles & roadmap
        career_roles = ml_career_roles or career_roles
        roadmap = [
            {'week': f"Step {r['step']}: {r['duration']}", 'action': f"{r['title']} — {r['desc']}"}
            for r in ml_skill_gap.get('roadmap', [])
        ] or roadmap

        ctx = {
            **_base_ctx(request, student),
            'career_intel_score': career_intel_score,
            'overall_readiness': overall_readiness,
            'overall_status': overall_status,
            'overall_status_class': overall_status_class,
            'overall_color': overall_color,
            'circle_offset': circle_offset,
            'predicted_salary_lpa': predicted_salary_lpa,
            'resume_score': resume_score,
            'profile_comp_score': profile_comp_score,
            'projects_count': projects_count,
            'featured_projects': featured_projects,
            'certs_count': certs_count,
            'missing_skills': ml_skill_gap.get('missing_skills', []),
            'profile_strength_cards': profile_strength_cards,
            'strengths': strengths,
            'improvements': improvements,
            'career_roles': career_roles,
            'roadmap': roadmap,
            'monthly_goals': monthly_goals,
            'timeline_trend': timeline_trend,
            'score_explanations': score_explanations,
            'trending_skills': trending_skills,

            # JSON Data strings for Chart.js
            'chart_readiness_labels_json': json.dumps(chart_readiness_labels),
            'chart_readiness_data_json': json.dumps(chart_readiness_data),
            'chart_skills_labels_json': json.dumps(chart_skills_labels),
            'chart_skills_data_json': json.dumps(chart_skills_data),
            'chart_tech_labels_json': json.dumps(chart_tech_labels),
            'chart_tech_data_json': json.dumps(chart_tech_data),
            'chart_salary_labels_json': json.dumps(chart_salary_labels),
            'chart_salary_data_json': json.dumps(chart_salary_data),
            'chart_growth_labels_json': json.dumps(chart_growth_labels),
            'chart_growth_data_json': json.dumps(chart_growth_data),
            'chart_learning_labels_json': json.dumps(chart_learning_labels),
            'chart_learning_data_json': json.dumps(chart_learning_data),
        }

        return render(request, self.template_name, ctx)


# ─────────────────────────────────────────────────────────────────────────────
# Career Analytics & Passport PDF View
# ─────────────────────────────────────────────────────────────────────────────

class StudentAnalyticsView(StudentRequiredMixin, View):
    """Displays student career analytics, scores, readiness gauges, application statistics, and salary predictions."""
    template_name = 'student_portal/analytics.html'

    def get(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        applications = Application.objects.filter(student=student).select_related('drive', 'drive__company')
        
        # Calculate stats
        total_apps = applications.count()
        total_interviews = applications.filter(status='SHORTLISTED').count()
        total_offers = applications.filter(status='SELECTED').count()

        # Gather scores
        ats_score = student.ats_score()
        readiness_score = student.placement_readiness()
        improvement_score = student.career_score()
        completion_score = student.profile_completion()

        # Compute dynamic Placement Probability
        cgpa_val = float(student.cgpa or 0)
        has_resume = 1 if student.resume else 0
        
        prob_score = (cgpa_val / 10.0 * 35) + (has_resume * 15) + (ats_score / 100.0 * 15) + (completion_score / 100.0 * 15) + (min(total_interviews * 5, 20))
        prob_score = round(min(max(prob_score, 0), 100))

        # Skill metrics count
        student_skills = set()
        if student.skills:
            for s in student.skills.split(','):
                if s.strip():
                    student_skills.add(s.strip().lower())
        for se in student.skill_entries.all():
            student_skills.add(se.name.strip().lower())
            
        active_resume = student.resume_versions.filter(is_active=True).first()
        if active_resume:
            try:
                r_skills = json.loads(active_resume.skills_found or '[]')
                for s in r_skills:
                    student_skills.add(s.strip().lower())
            except Exception:
                pass

        total_skills = len(student_skills)

        # ─── SALARY PREDICTION MATRIX ───
        # Base fresher package from CGPA (minimum 5.0 LPA baseline)
        cgpa_pred_val = float(student.cgpa or 6.5)
        base_salary = round(max(cgpa_pred_val * 0.8, 5.0), 2)

        skill_premiums = {
            'cloud': {
                'keywords': ['aws', 'cloud', 'gcp', 'azure', 'docker', 'kubernetes', 'jenkins', 'devops', 'ci/cd'],
                'amount': 1.5,
                'max_limit': 4.0,
                'label': 'Cloud & DevOps'
            },
            'languages': {
                'keywords': ['python', 'java', 'go', 'golang', 'c++', 'rust', 'ruby', 'swift', 'typescript'],
                'amount': 1.0,
                'max_limit': 3.0,
                'label': 'Programming Languages'
            },
            'frameworks': {
                'keywords': ['django', 'react', 'node', 'express', 'angular', 'vue', 'spring', 'flask', 'laravel'],
                'amount': 1.2,
                'max_limit': 3.0,
                'label': 'Frameworks'
            },
            'databases': {
                'keywords': ['sql', 'postgresql', 'mongodb', 'mysql', 'oracle', 'redis', 'cassandra', 'database'],
                'amount': 0.8,
                'max_limit': 2.0,
                'label': 'Databases'
            },
            'data_science': {
                'keywords': ['machine learning', 'deep learning', 'pandas', 'numpy', 'tensorflow', 'pytorch', 'scikit-learn', 'data science', 'ai'],
                'amount': 1.5,
                'max_limit': 4.0,
                'label': 'Data Science & AI'
            }
        }

        total_premium = 0.0
        applied_premiums = []

        for key, config in skill_premiums.items():
            matched_in_category = []
            for skill in student_skills:
                if skill in config['keywords']:
                    matched_in_category.append(skill.title())
            
            if matched_in_category:
                earned = len(matched_in_category) * config['amount']
                earned = min(earned, config['max_limit'])
                total_premium += earned
                applied_premiums.append({
                    'category': config['label'],
                    'matched': matched_in_category,
                    'earned': round(earned, 2)
                })

        predicted_salary = base_salary + total_premium
        predicted_min = round(max(predicted_salary - 0.75, 4.5), 2)
        predicted_max = round(predicted_salary + 1.25, 2)

        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'ats_score': ats_score,
            'readiness_score': readiness_score,
            'improvement_score': improvement_score,
            'completion_score': completion_score,
            'total_apps': total_apps,
            'total_interviews': total_interviews,
            'total_offers': total_offers,
            'placement_probability': prob_score,
            'total_skills': total_skills,
            'applications': applications[:5],
            
            # Salary Prediction details
            'salary_min': predicted_min,
            'salary_max': predicted_max,
            'base_salary': base_salary,
            'applied_premiums': applied_premiums,
            'total_premium': round(total_premium, 2)
        })


class StudentCareerPassportPdfView(StudentRequiredMixin, View):
    """Generates a professional recruiter-friendly Career Passport PDF using ReportLab."""
    def get(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        import io
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        story = []
        styles = getSampleStyleSheet()

        # Custom paragraph styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=24,
            leading=28,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#4b5563'),
            spaceAfter=15
        )
        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            textColor=colors.HexColor('#111827'),
            spaceBefore=14,
            spaceAfter=6,
            keepWithNext=True
        )
        body_text = ParagraphStyle(
            'BodyTextCustom',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor('#374151')
        )
        meta_label = ParagraphStyle(
            'MetaLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor('#1f2937')
        )

        # 1. Header Information
        story.append(Paragraph(student.name, title_style))
        contact_info = f"Roll No: {student.roll_number} | Email: {student.email} | Phone: {student.phone or 'N/A'}"
        story.append(Paragraph(contact_info, subtitle_style))

        # Bio Section
        if student.bio:
            story.append(Paragraph("<b>Professional Summary</b>", section_heading))
            story.append(Paragraph(student.bio, body_text))
            story.append(Spacer(1, 10))

        # 2. Academic Summary Table
        story.append(Paragraph("<b>Academic Details</b>", section_heading))
        academics_data = [
            [
                Paragraph("<b>Department:</b>", meta_label), Paragraph(student.department.name, body_text),
                Paragraph("<b>Batch:</b>", meta_label), Paragraph(student.batch.name, body_text)
            ],
            [
                Paragraph("<b>Current Semester:</b>", meta_label), Paragraph(str(student.semester), body_text),
                Paragraph("<b>CGPA / SPI / CPI:</b>", meta_label), Paragraph(f"{student.cgpa or 'N/A'} / {student.spi or 'N/A'} / {student.cpi or 'N/A'}", body_text)
            ],
            [
                Paragraph("<b>Division:</b>", meta_label), Paragraph(student.division or 'N/A', body_text),
                Paragraph("<b>Active Backlogs:</b>", meta_label), Paragraph(str(student.backlogs), body_text)
            ]
        ]
        academics_table = Table(academics_data, colWidths=[120, 150, 110, 150])
        academics_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f9fafb')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 6),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#f3f4f6')),
        ]))
        story.append(academics_table)
        story.append(Spacer(1, 12))

        # 3. Career Scores Overview
        story.append(Paragraph("<b>Career Scores & Preparedness</b>", section_heading))
        scores_data = [
            [
                Paragraph("<b>ATS Score:</b>", meta_label), Paragraph(f"{student.ats_score()}%", body_text),
                Paragraph("<b>Placement Readiness:</b>", meta_label), Paragraph(f"{student.placement_readiness()}%", body_text)
            ],
            [
                Paragraph("<b>Profile Completion:</b>", meta_label), Paragraph(f"{student.profile_completion()}%", body_text),
                Paragraph("<b>Career Improvement:</b>", meta_label), Paragraph(f"{student.career_score()}%", body_text)
            ]
        ]
        scores_table = Table(scores_data, colWidths=[120, 150, 110, 150])
        scores_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f9fafb')),
            ('PADDING', (0,0), (-1,-1), 6),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#f3f4f6')),
        ]))
        story.append(scores_table)
        story.append(Spacer(1, 12))

        # 4. Resume & Skills info
        active_resume = student.resume_versions.filter(is_active=True).first()
        student_skills = []
        if student.skills:
            student_skills = [s.strip() for s in student.skills.split(',') if s.strip()]
        for se in student.skill_entries.all():
            if se.name not in student_skills:
                student_skills.append(se.name)

        if active_resume:
            try:
                r_skills = json.loads(active_resume.skills_found or '[]')
                for s in r_skills:
                    if s not in student_skills:
                        student_skills.append(s)
            except Exception:
                pass

        story.append(Paragraph("<b>Skills Inventory</b>", section_heading))
        skills_text = ", ".join(student_skills) if student_skills else "No skills listed."
        story.append(Paragraph(skills_text, body_text))
        story.append(Spacer(1, 10))

        # Projects and Certificates (Parsed from Resume Analysis)
        if active_resume:
            try:
                projects = json.loads(active_resume.projects_found or '[]')
                if projects:
                    story.append(Paragraph("<b>Highlighted Projects</b>", section_heading))
                    for proj in projects:
                        story.append(Paragraph(f"• {proj}", body_text))
                    story.append(Spacer(1, 10))
            except Exception:
                pass

            try:
                certs = json.loads(active_resume.certificates_found or '[]')
                if certs:
                    story.append(Paragraph("<b>Professional Certificates</b>", section_heading))
                    for cert in certs:
                        story.append(Paragraph(f"• {cert}", body_text))
                    story.append(Spacer(1, 10))
            except Exception:
                pass

        # 5. Coding Profiles
        story.append(Paragraph("<b>Professional Profiles & Portfolios</b>", section_heading))
        profiles_data = [
            [Paragraph("<b>LinkedIn:</b>", meta_label), Paragraph(student.linkedin_url or 'N/A', body_text)],
            [Paragraph("<b>GitHub:</b>", meta_label), Paragraph(student.github_url or 'N/A', body_text)],
            [Paragraph("<b>Portfolio:</b>", meta_label), Paragraph(student.portfolio_url or 'N/A', body_text)]
        ]
        profiles_table = Table(profiles_data, colWidths=[120, 410])
        profiles_table.setStyle(TableStyle([
            ('PADDING', (0,0), (-1,-1), 4),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#f3f4f6')),
        ]))
        story.append(profiles_table)
        story.append(Spacer(1, 12))

        # 6. Placement Application History
        apps = Application.objects.filter(student=student).select_related('drive', 'drive__company').order_by('-applied_at')
        if apps.exists():
            story.append(Paragraph("<b>Application History</b>", section_heading))
            app_table_data = [[
                Paragraph("<b>Company</b>", meta_label),
                Paragraph("<b>Role</b>", meta_label),
                Paragraph("<b>Date Applied</b>", meta_label),
                Paragraph("<b>Status</b>", meta_label)
            ]]
            for app in apps:
                app_table_data.append([
                    Paragraph(app.drive.company.name, body_text),
                    Paragraph(app.drive.role, body_text),
                    Paragraph(app.applied_at.strftime('%b %d, %Y'), body_text),
                    Paragraph(app.get_status_display(), body_text)
                ])

            app_table = Table(app_table_data, colWidths=[150, 160, 110, 110])
            app_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f3f4f6')),
                ('PADDING', (0,0), (-1,-1), 6),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f9fafb')])
            ]))
            story.append(KeepTogether(app_table))

        doc.build(story)
        buffer.seek(0)
        
        filename = f"Career_Passport_{student.roll_number}.pdf"
        return FileResponse(buffer, as_attachment=True, filename=filename, content_type='application/pdf')


# ─────────────────────────────────────────────────────────────────────────────
# Project Portfolio Views
# ─────────────────────────────────────────────────────────────────────────────

class StudentProjectsListView(StudentRequiredMixin, View):
    template_name = 'student_portal/projects_list.html'

    def get(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        # Base projects query
        projects = Project.objects.filter(student=student)

        # GET Search & Filter arguments
        q = request.GET.get('q', '').strip()
        category = request.GET.get('category', '').strip()
        status = request.GET.get('status', '').strip()

        if q:
            projects = projects.filter(
                Q(title__icontains=q) |
                Q(technologies__icontains=q) |
                Q(short_description__icontains=q)
            )
        if category:
            projects = projects.filter(category=category)
        if status:
            projects = projects.filter(status=status)

        # Pre-order: featured first, then created date descending
        projects = projects.order_by('-is_featured', '-created_at')

        # Stats calculations
        total_projects = Project.objects.filter(student=student).count()
        completed_projects = Project.objects.filter(student=student, status='COMPLETED').count()
        ongoing_projects = Project.objects.filter(student=student, status='ONGOING').count()
        featured_projects = Project.objects.filter(student=student, is_featured=True).count()
        
        # Portfolio Score: Average score of all projects
        avg_score = 0
        all_student_projects = Project.objects.filter(student=student)
        if all_student_projects.exists():
            avg_score = round(sum(p.portfolio_score for p in all_student_projects) / all_student_projects.count())

        recent_project = all_student_projects.order_by('-created_at').first()

        context = {
            **_base_ctx(request, student),
            'projects': projects,
            'total_projects': total_projects,
            'completed_projects': completed_projects,
            'ongoing_projects': ongoing_projects,
            'featured_projects': featured_projects,
            'portfolio_score': avg_score,
            'recent_project': recent_project,
            'categories': Project.Category.choices,
            'statuses': Project.Status.choices,
            'q': q,
            'selected_category': category,
            'selected_status': status,
        }
        return render(request, self.template_name, context)


class StudentProjectCreateView(StudentRequiredMixin, View):
    template_name = 'student_portal/project_form.html'

    def get(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')
        form = ProjectForm()
        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'form': form,
            'is_edit': False,
        })

    def post(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=False)
            project.student = student
            # If marked as featured, optionally unfeature other projects of this student
            if project.is_featured:
                Project.objects.filter(student=student, is_featured=True).update(is_featured=False)
            project.save()
            messages.success(request, f"Project '{project.title}' added successfully.")
            return redirect('student_portal:projects_list')
        
        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'form': form,
            'is_edit': False,
        })


class StudentProjectUpdateView(StudentRequiredMixin, View):
    template_name = 'student_portal/project_form.html'

    def get(self, request, pk, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        project = get_object_or_404(Project, pk=pk, student=student)
        form = ProjectForm(instance=project)
        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'form': form,
            'project': project,
            'is_edit': True,
        })

    def post(self, request, pk, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        project = get_object_or_404(Project, pk=pk, student=student)
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            updated_project = form.save(commit=False)
            # If marked as featured, unfeature other projects of this student
            if updated_project.is_featured:
                Project.objects.filter(student=student, is_featured=True).exclude(pk=project.pk).update(is_featured=False)
            updated_project.save()
            messages.success(request, f"Project '{updated_project.title}' updated successfully.")
            return redirect('student_portal:projects_list')

        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'form': form,
            'project': project,
            'is_edit': True,
        })


class StudentProjectDeleteView(StudentRequiredMixin, View):
    template_name = 'student_portal/project_confirm_delete.html'

    def get(self, request, pk, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        project = get_object_or_404(Project, pk=pk, student=student)
        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'project': project,
        })

    def post(self, request, pk, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        project = get_object_or_404(Project, pk=pk, student=student)
        title = project.title
        project.delete()
        messages.success(request, f"Project '{title}' has been deleted.")
        return redirect('student_portal:projects_list')


class StudentProjectDetailView(StudentRequiredMixin, View):
    template_name = 'student_portal/project_detail.html'

    def get(self, request, pk, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        project = get_object_or_404(Project, pk=pk, student=student)
        
        # Portfolio Score breakdown check
        score_breakdown = {
            'github_completed': bool(project.github_url),
            'live_completed': bool(project.live_url),
            'doc_completed': bool(project.documentation_url),
            'desc_completed': bool(project.detailed_description and len(project.detailed_description.strip()) > 0),
            'tech_completed': len(project.technology_list) >= 5,
            'video_completed': bool(project.youtube_url),
            'featured_completed': project.is_featured,
        }

        context = {
            **_base_ctx(request, student),
            'project': project,
            'score_breakdown': score_breakdown,
            'is_recruiter': False,
        }
        return render(request, self.template_name, context)


class RecruiterPortfolioView(LoginRequiredMixin, View):
    template_name = 'student_portal/projects_list.html'

    def get(self, request, student_id, *args, **kwargs):
        # Allow any authenticated user (e.g. COLLEGE_ADMIN, Recruiters)
        student = get_object_or_404(Student, pk=student_id)
        
        # Recruiter view: show projects list of student, read-only
        projects = Project.objects.filter(student=student).order_by('-is_featured', '-created_at')

        # GET Search & Filter arguments
        q = request.GET.get('q', '').strip()
        category = request.GET.get('category', '').strip()
        status = request.GET.get('status', '').strip()

        if q:
            projects = projects.filter(
                Q(title__icontains=q) |
                Q(technologies__icontains=q) |
                Q(short_description__icontains=q)
            )
        if category:
            projects = projects.filter(category=category)
        if status:
            projects = projects.filter(status=status)

        total_projects = projects.count()
        completed_projects = projects.filter(status='COMPLETED').count()
        ongoing_projects = projects.filter(status='ONGOING').count()
        featured_projects = projects.filter(is_featured=True).count()
        
        avg_score = 0
        all_student_projects = Project.objects.filter(student=student)
        if all_student_projects.exists():
            avg_score = round(sum(p.portfolio_score for p in all_student_projects) / all_student_projects.count())

        recent_project = all_student_projects.order_by('-created_at').first()

        context = {
            'student': student,
            'projects': projects,
            'total_projects': total_projects,
            'completed_projects': completed_projects,
            'ongoing_projects': ongoing_projects,
            'featured_projects': featured_projects,
            'portfolio_score': avg_score,
            'recent_project': recent_project,
            'categories': Project.Category.choices,
            'statuses': Project.Status.choices,
            'q': q,
            'selected_category': category,
            'selected_status': status,
            'is_recruiter': True,
        }
        return render(request, self.template_name, context)


class RecruiterProjectDetailView(LoginRequiredMixin, View):
    template_name = 'student_portal/project_detail.html'

    def get(self, request, pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=pk)
        
        # Portfolio Score breakdown check
        score_breakdown = {
            'github_completed': bool(project.github_url),
            'live_completed': bool(project.live_url),
            'doc_completed': bool(project.documentation_url),
            'desc_completed': bool(project.detailed_description and len(project.detailed_description.strip()) > 0),
            'tech_completed': len(project.technology_list) >= 5,
            'video_completed': bool(project.youtube_url),
            'featured_completed': project.is_featured,
        }

        context = {
            'student': project.student,
            'project': project,
            'score_breakdown': score_breakdown,
            'is_recruiter': True,
        }
        return render(request, self.template_name, context)


# ─────────────────────────────────────────────────────────────────────────────
# Developer Journey Helper Functions & Views
# ─────────────────────────────────────────────────────────────────────────────

def _get_journey_stats(student):
    today = datetime.date.today()
    this_year = today.year

    # Fetch unique dates of activities
    active_dates_qs = Activity.objects.filter(student=student).values_list('date', flat=True).distinct().order_by('-date')
    active_dates = sorted(list(set(active_dates_qs)), reverse=True)

    # Current Streak
    current_streak = 0
    if active_dates:
        if active_dates[0] == today or active_dates[0] == today - datetime.timedelta(days=1):
            current_streak = 1
            curr_date = active_dates[0]
            for next_date in active_dates[1:]:
                if curr_date - next_date == datetime.timedelta(days=1):
                    current_streak += 1
                    curr_date = next_date
                else:
                    break

    # Longest Streak
    longest_streak = 0
    if active_dates:
        asc_dates = sorted(active_dates)
        temp_streak = 1
        longest_streak = 1
        for i in range(1, len(asc_dates)):
            if asc_dates[i] - asc_dates[i-1] == datetime.timedelta(days=1):
                temp_streak += 1
            elif asc_dates[i] != asc_dates[i-1]:
                longest_streak = max(longest_streak, temp_streak)
                temp_streak = 1
        longest_streak = max(longest_streak, temp_streak)

    # Consistency Score (Active days in last 30 days)
    thirty_days_ago = today - datetime.timedelta(days=30)
    active_days_last_30 = Activity.objects.filter(
        student=student,
        date__range=[thirty_days_ago, today]
    ).values('date').distinct().count()
    consistency_score = min(100, round((active_days_last_30 / 30.0) * 100))

    # General Stats
    activities_this_year = Activity.objects.filter(student=student, date__year=this_year).count()
    weekly_updates = WeeklySummary.objects.filter(student=student, date__year=this_year).count()
    monthly_updates = MonthlySummary.objects.filter(student=student, date__year=this_year).count()
    hackathons_count = HackathonJournal.objects.filter(student=student).count()
    
    # Calculate learning hours
    learning_hours_val = Activity.objects.filter(
        student=student,
        category__in=['LEARNING', 'CODING_PRACTICE', 'WORKSHOP']
    ).aggregate(total=Sum('hours_spent'))['total'] or 0
    learning_hours = float(learning_hours_val)

    # Problems solved
    problems_solved = CodingPractice.objects.filter(student=student).aggregate(total=Sum('problems_solved'))['total'] or 0
    
    # Milestones
    milestones_count = ProjectMilestone.objects.filter(student=student).count()

    # Goals completed
    goals_completed = LearningGoal.objects.filter(student=student, status='COMPLETED').count()

    # Points & Growth Level
    points = (Activity.objects.filter(student=student).count() * 5) + (learning_hours * 2) + (problems_solved * 1) + (hackathons_count * 20) + (milestones_count * 10) + (goals_completed * 15)
    
    if points <= 50:
        level = "🌱 Beginner"
    elif points <= 150:
        level = "🌿 Consistent Learner"
    elif points <= 300:
        level = "🌳 Active Developer"
    elif points <= 500:
        level = "🚀 Placement Ready"
    else:
        level = "👑 Industry Ready"

    return {
        'current_streak': current_streak,
        'longest_streak': longest_streak,
        'consistency_score': consistency_score,
        'activities_this_year': activities_this_year,
        'weekly_updates': weekly_updates,
        'monthly_updates': monthly_updates,
        'hackathons_count': hackathons_count,
        'learning_hours': learning_hours,
        'problems_solved': problems_solved,
        'milestones_count': milestones_count,
        'goals_completed': goals_completed,
        'points': points,
        'growth_level': level
    }


def _get_available_years(student):
    """Return a descending list of calendar years that have at least one
    activity, always including the current year even if it has none yet."""
    years = {d.year for d in Activity.objects.filter(student=student).dates('date', 'year')}
    years.add(datetime.date.today().year)
    return sorted(years, reverse=True)


def _resolve_selected_year(request, available_years):
    """Read ?year= from the request and make sure it's a valid choice."""
    current_year = datetime.date.today().year
    try:
        selected_year = int(request.GET.get('year', current_year))
    except (TypeError, ValueError):
        selected_year = current_year
    if selected_year not in available_years:
        selected_year = current_year if current_year in available_years else available_years[0]
    return selected_year


def _get_heatmap_cols(student, year):
    start_date = datetime.date(year, 1, 1)
    weekday = start_date.weekday()
    if weekday < 6:
        start_date -= datetime.timedelta(days=weekday + 1)
    
    end_date = datetime.date(year, 12, 31)
    end_weekday = end_date.weekday()
    if end_weekday < 5:
        end_date += datetime.timedelta(days=5 - end_weekday)
    elif end_weekday == 6:
        end_date += datetime.timedelta(days=6)

    from django.db.models import Count
    activity_counts = Activity.objects.filter(
        student=student,
        date__year=year
    ).values('date').annotate(count=Count('id'))
    counts_dict = {item['date']: item['count'] for item in activity_counts}

    columns = []
    curr = start_date
    while curr <= end_date:
        col_days = []
        for _ in range(7):
            count = counts_dict.get(curr, 0)
            if count == 0:
                color = '#E2E8F0'
            elif count <= 2:
                color = '#9BE9A8'
            elif count <= 4:
                color = '#40C463'
            elif count <= 6:
                color = '#30A14E'
            else:
                color = '#216E39'
            col_days.append({
                'date': curr,
                'count': count,
                'color': color,
                'is_current_year': curr.year == year,
            })
            curr += datetime.timedelta(days=1)
        columns.append(col_days)
    return columns


class DeveloperJourneyListView(StudentRequiredMixin, View):
    template_name = 'student_portal/journey_list.html'

    def get(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        available_years = _get_available_years(student)
        selected_year = _resolve_selected_year(request, available_years)

        heatmap_cols = _get_heatmap_cols(student, selected_year)
        selected_year_activity_count = Activity.objects.filter(
            student=student, date__year=selected_year
        ).count()

        date_str = request.GET.get('date', '').strip()
        category_filter = request.GET.get('category', '').strip()

        activities = Activity.objects.filter(student=student)

        if date_str:
            try:
                clicked_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                activities = activities.filter(date=clicked_date)
            except ValueError:
                pass

        if category_filter:
            activities = activities.filter(category=category_filter)

        links, created = TechnicalLinks.objects.get_or_create(student=student)
        goals = LearningGoal.objects.filter(student=student)
        achievements = DeveloperAchievement.objects.filter(student=student)

        stats = _get_journey_stats(student)

        context = {
            **_base_ctx(request, student),
            'heatmap_cols': heatmap_cols,
            'activities': activities,
            'links': links,
            'goals': goals,
            'achievements': achievements,
            'date_filter': date_str,
            'category_filter': category_filter,
            'available_years': available_years,
            'selected_year': selected_year,
            'selected_year_activity_count': selected_year_activity_count,
            'categories': Activity.Category.choices,
            'is_recruiter': False,
            **stats
        }
        return render(request, self.template_name, context)


FORM_MAP = {
    'daily_log': (ActivityForm, Activity),
    'weekly_summary': (WeeklySummaryForm, WeeklySummary),
    'monthly_summary': (MonthlySummaryForm, MonthlySummary),
    'project_milestone': (ProjectMilestoneForm, ProjectMilestone),
    'hackathon': (HackathonJournalForm, HackathonJournal),
    'coding_practice': (CodingPracticeForm, CodingPractice),
    'learning_journal': (LearningJournalForm, LearningJournal),
    'open_source': (OpenSourceContributionForm, OpenSourceContribution),
    'goal': (LearningGoalForm, LearningGoal),
    'achievement': (DeveloperAchievementForm, DeveloperAchievement),
}


class AddJourneyActivityView(StudentRequiredMixin, View):
    template_name = 'student_portal/journey_form.html'

    def get(self, request, activity_type, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        if activity_type not in FORM_MAP:
            messages.error(request, "Invalid activity type.")
            return redirect('student_portal:journey')

        form_class, model_class = FORM_MAP[activity_type]
        
        if activity_type == 'project_milestone':
            form = form_class(student=student)
        else:
            form = form_class()

        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'form': form,
            'activity_type': activity_type,
            'is_edit': False,
            'title_prefix': f"Add {activity_type.replace('_', ' ').title()}"
        })

    def post(self, request, activity_type, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        if activity_type not in FORM_MAP:
            messages.error(request, "Invalid activity type.")
            return redirect('student_portal:journey')

        form_class, model_class = FORM_MAP[activity_type]
        
        if activity_type == 'project_milestone':
            form = form_class(request.POST, request.FILES, student=student)
        else:
            form = form_class(request.POST, request.FILES)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.student = student
            obj.save()
            messages.success(request, f"{activity_type.replace('_', ' ').title()} recorded successfully.")
            return redirect('student_portal:journey')

        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'form': form,
            'activity_type': activity_type,
            'is_edit': False,
            'title_prefix': f"Add {activity_type.replace('_', ' ').title()}"
        })


class EditJourneyActivityView(StudentRequiredMixin, View):
    template_name = 'student_portal/journey_form.html'

    def get(self, request, activity_type, pk, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        if activity_type not in FORM_MAP:
            messages.error(request, "Invalid activity type.")
            return redirect('student_portal:journey')

        form_class, model_class = FORM_MAP[activity_type]
        obj = get_object_or_404(model_class, pk=pk, student=student)
        
        if activity_type == 'project_milestone':
            form = form_class(instance=obj, student=student)
        else:
            form = form_class(instance=obj)

        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'form': form,
            'activity_type': activity_type,
            'is_edit': True,
            'title_prefix': f"Edit {activity_type.replace('_', ' ').title()}"
        })

    def post(self, request, activity_type, pk, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        if activity_type not in FORM_MAP:
            messages.error(request, "Invalid activity type.")
            return redirect('student_portal:journey')

        form_class, model_class = FORM_MAP[activity_type]
        obj = get_object_or_404(model_class, pk=pk, student=student)

        if activity_type == 'project_milestone':
            form = form_class(request.POST, request.FILES, instance=obj, student=student)
        else:
            form = form_class(request.POST, request.FILES, instance=obj)

        if form.is_valid():
            form.save()
            messages.success(request, f"{activity_type.replace('_', ' ').title()} updated successfully.")
            return redirect('student_portal:journey')

        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'form': form,
            'activity_type': activity_type,
            'is_edit': True,
            'title_prefix': f"Edit {activity_type.replace('_', ' ').title()}"
        })


class DeleteJourneyActivityView(StudentRequiredMixin, View):
    template_name = 'student_portal/journey_confirm_delete.html'

    def get(self, request, activity_type, pk, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        if activity_type not in FORM_MAP:
            messages.error(request, "Invalid activity type.")
            return redirect('student_portal:journey')

        form_class, model_class = FORM_MAP[activity_type]
        obj = get_object_or_404(model_class, pk=pk, student=student)
        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'object': obj,
            'activity_type': activity_type,
        })

    def post(self, request, activity_type, pk, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        if activity_type not in FORM_MAP:
            messages.error(request, "Invalid activity type.")
            return redirect('student_portal:journey')

        form_class, model_class = FORM_MAP[activity_type]
        obj = get_object_or_404(model_class, pk=pk, student=student)
        obj.delete()
        messages.success(request, f"{activity_type.replace('_', ' ').title()} has been deleted.")
        return redirect('student_portal:journey')


class TechnicalLinksUpdateView(StudentRequiredMixin, View):
    template_name = 'student_portal/journey_form.html'

    def get(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        links, created = TechnicalLinks.objects.get_or_create(student=student)
        form = TechnicalLinksForm(instance=links)
        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'form': form,
            'is_edit': True,
            'title_prefix': 'Update Technical Links'
        })

    def post(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        links, created = TechnicalLinks.objects.get_or_create(student=student)
        form = TechnicalLinksForm(request.POST, instance=links)
        if form.is_valid():
            form.save()
            messages.success(request, "Technical links updated successfully.")
            return redirect('student_portal:journey')

        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'form': form,
            'is_edit': True,
            'title_prefix': 'Update Technical Links'
        })


class RecruiterDeveloperJourneyView(LoginRequiredMixin, View):
    template_name = 'student_portal/journey_list.html'

    def get(self, request, student_id, *args, **kwargs):
        student = get_object_or_404(Student, pk=student_id)

        available_years = _get_available_years(student)
        selected_year = _resolve_selected_year(request, available_years)

        heatmap_cols = _get_heatmap_cols(student, selected_year)
        selected_year_activity_count = Activity.objects.filter(
            student=student, date__year=selected_year
        ).count()

        date_str = request.GET.get('date', '').strip()
        category_filter = request.GET.get('category', '').strip()

        activities = Activity.objects.filter(student=student)

        if date_str:
            try:
                clicked_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                activities = activities.filter(date=clicked_date)
            except ValueError:
                pass

        if category_filter:
            activities = activities.filter(category=category_filter)

        links, created = TechnicalLinks.objects.get_or_create(student=student)
        goals = LearningGoal.objects.filter(student=student)
        achievements = DeveloperAchievement.objects.filter(student=student)

        stats = _get_journey_stats(student)

        context = {
            'student': student,
            'heatmap_cols': heatmap_cols,
            'activities': activities,
            'links': links,
            'goals': goals,
            'achievements': achievements,
            'date_filter': date_str,
            'category_filter': category_filter,
            'available_years': available_years,
            'selected_year': selected_year,
            'selected_year_activity_count': selected_year_activity_count,
            'categories': Activity.Category.choices,
            'is_recruiter': True,
            **stats
        }
        return render(request, self.template_name, context)


# ─────────────────────────────────────────────────────────────────────────────
# Certificates Module Views
# ─────────────────────────────────────────────────────────────────────────────
from django.core.paginator import Paginator

class StudentCertificatesListView(LoginRequiredMixin, View):
    template_name = 'student_portal/certificates_list.html'

    def get(self, request, *args, **kwargs):
        student = request.user.student_profile
        
        # Get all student certificates
        qs = Certificate.objects.filter(student=student)

        # Calculate Summary Card Stats
        total_count = qs.count()
        courses_count = qs.filter(purpose='COURSE_COMPLETION').count()
        hackathons_count = qs.filter(purpose='HACKATHON').count()
        workshops_count = qs.filter(purpose='WORKSHOP').count()

        # Handle Search
        q = request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(issuing_organization__icontains=q) |
                Q(purpose__icontains=q)
            )

        # Handle Filters
        purpose = request.GET.get('purpose', '').strip()
        if purpose:
            qs = qs.filter(purpose=purpose)

        year = request.GET.get('year', '').strip()
        if year:
            try:
                qs = qs.filter(issue_date__year=int(year))
            except ValueError:
                pass

        sort = request.GET.get('sort', 'newest').strip()
        if sort == 'oldest':
            qs = qs.order_by('issue_date', 'created_at')
        else:
            qs = qs.order_by('-issue_date', '-created_at')

        # Pagination
        paginator = Paginator(qs, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Get list of unique years for the filter dropdown
        years = Certificate.objects.filter(student=student).values_list('issue_date__year', flat=True).distinct().order_by('-issue_date__year')

        context = {
            'student': student,
            'page_obj': page_obj,
            'total_count': total_count,
            'courses_count': courses_count,
            'hackathons_count': hackathons_count,
            'workshops_count': workshops_count,
            'q': q,
            'selected_purpose': purpose,
            'selected_year': year,
            'selected_sort': sort,
            'years': years,
            'purposes': Certificate.Purpose.choices,
            'is_recruiter': False,
        }
        return render(request, self.template_name, context)


class StudentCertificateCreateView(LoginRequiredMixin, View):
    form_class = CertificateForm
    template_name = 'student_portal/certificate_form.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {
            'form': form,
            'title_prefix': 'Add Certificate',
            'is_edit': False
        })

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            certificate = form.save(commit=False)
            certificate.student = request.user.student_profile
            certificate.save()
            messages.success(request, "Certificate added successfully!")
            return redirect('student_portal:certificates_list')
        return render(request, self.template_name, {
            'form': form,
            'title_prefix': 'Add Certificate',
            'is_edit': False
        })


class StudentCertificateDetailView(LoginRequiredMixin, View):
    template_name = 'student_portal/certificate_detail.html'

    def get(self, request, pk, *args, **kwargs):
        student = request.user.student_profile
        certificate = get_object_or_404(Certificate, pk=pk, student=student)
        return render(request, self.template_name, {
            'certificate': certificate,
            'is_recruiter': False
        })


class StudentCertificateUpdateView(LoginRequiredMixin, View):
    form_class = CertificateForm
    template_name = 'student_portal/certificate_form.html'

    def get(self, request, pk, *args, **kwargs):
        student = request.user.student_profile
        certificate = get_object_or_404(Certificate, pk=pk, student=student)
        form = self.form_class(instance=certificate)
        return render(request, self.template_name, {
            'form': form,
            'title_prefix': 'Edit Certificate',
            'is_edit': True,
            'certificate': certificate
        })

    def post(self, request, pk, *args, **kwargs):
        student = request.user.student_profile
        certificate = get_object_or_404(Certificate, pk=pk, student=student)
        form = self.form_class(request.POST, request.FILES, instance=certificate)
        if form.is_valid():
            form.save()
            messages.success(request, "Certificate updated successfully!")
            return redirect('student_portal:certificate_detail', pk=pk)
        return render(request, self.template_name, {
            'form': form,
            'title_prefix': 'Edit Certificate',
            'is_edit': True,
            'certificate': certificate
        })


class StudentCertificateDeleteView(LoginRequiredMixin, View):
    template_name = 'student_portal/certificate_confirm_delete.html'

    def get(self, request, pk, *args, **kwargs):
        student = request.user.student_profile
        certificate = get_object_or_404(Certificate, pk=pk, student=student)
        return render(request, self.template_name, {'object': certificate})

    def post(self, request, pk, *args, **kwargs):
        student = request.user.student_profile
        certificate = get_object_or_404(Certificate, pk=pk, student=student)
        certificate.delete()
        messages.success(request, "Certificate removed successfully!")
        return redirect('student_portal:certificates_list')


# Recruiter Views (Read-Only)

class RecruiterCertificatesListView(LoginRequiredMixin, View):
    template_name = 'student_portal/certificates_list.html'

    def get(self, request, student_id, *args, **kwargs):
        student = get_object_or_404(Student, id=student_id)
        
        # Recruiter gets read-only list
        qs = Certificate.objects.filter(student=student)

        # Calculate Summary Card Stats
        total_count = qs.count()
        courses_count = qs.filter(purpose='COURSE_COMPLETION').count()
        hackathons_count = qs.filter(purpose='HACKATHON').count()
        workshops_count = qs.filter(purpose='WORKSHOP').count()

        # Search
        q = request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(issuing_organization__icontains=q) |
                Q(purpose__icontains=q)
            )

        # Filters
        purpose = request.GET.get('purpose', '').strip()
        if purpose:
            qs = qs.filter(purpose=purpose)

        year = request.GET.get('year', '').strip()
        if year:
            try:
                qs = qs.filter(issue_date__year=int(year))
            except ValueError:
                pass

        sort = request.GET.get('sort', 'newest').strip()
        if sort == 'oldest':
            qs = qs.order_by('issue_date', 'created_at')
        else:
            qs = qs.order_by('-issue_date', '-created_at')

        # Pagination
        paginator = Paginator(qs, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        years = Certificate.objects.filter(student=student).values_list('issue_date__year', flat=True).distinct().order_by('-issue_date__year')

        context = {
            'student': student,
            'page_obj': page_obj,
            'total_count': total_count,
            'courses_count': courses_count,
            'hackathons_count': hackathons_count,
            'workshops_count': workshops_count,
            'q': q,
            'selected_purpose': purpose,
            'selected_year': year,
            'selected_sort': sort,
            'years': years,
            'purposes': Certificate.Purpose.choices,
            'is_recruiter': True,
        }
        return render(request, self.template_name, context)


class RecruiterCertificateDetailView(LoginRequiredMixin, View):
    template_name = 'student_portal/certificate_detail.html'

    def get(self, request, pk, *args, **kwargs):
        certificate = get_object_or_404(Certificate, pk=pk)
        return render(request, self.template_name, {
            'certificate': certificate,
            'is_recruiter': True,
            'student': certificate.student
        })


class StudentCertificatePreviewView(StudentRequiredMixin, View):
    """Streams certificate file (PDF/Image) inline for browser viewing."""
    def get(self, request, pk, *args, **kwargs):
        student = _get_student(request)
        cert = get_object_or_404(Certificate, pk=pk, student=student)
        if not cert.certificate_file:
            messages.error(request, "Certificate file not found.")
            return redirect('student_portal:certificates_list')
        
        file_path = cert.certificate_file.path
        filename = os.path.basename(file_path)
        content_type = 'application/pdf' if filename.lower().endswith('.pdf') else 'image/jpeg'
        response = FileResponse(cert.certificate_file.open('rb'), content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response


class StudentCertificateDownloadView(StudentRequiredMixin, View):
    """Downloads certificate file."""
    def get(self, request, pk, *args, **kwargs):
        student = _get_student(request)
        cert = get_object_or_404(Certificate, pk=pk, student=student)
        if not cert.certificate_file:
            messages.error(request, "Certificate file not found.")
            return redirect('student_portal:certificates_list')
        
        filename = os.path.basename(cert.certificate_file.path)
        response = FileResponse(cert.certificate_file.open('rb'))
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class StudentCareerProfileView(StudentRequiredMixin, View):
    """Manages Career Profile settings (Job Role, Industry, City, Work Preference, Expected Salary, Relocation)."""
    template_name = 'student_portal/career_profile.html'

    def get(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')
        form = CareerProfileForm(instance=student)
        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'form': form,
        })

    def post(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')
        form = CareerProfileForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "Career Profile preferences updated successfully!")
            return redirect('student_portal:career_profile')
        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'form': form,
        })


from .resume_parser_service import parse_resume_file, sync_extracted_data_to_profile

class StudentAIResumeParserView(StudentRequiredMixin, View):
    """
    AI Resume Parser:
    Lists student uploaded resumes, parses structured entity data (Skills, Programming Languages,
    Tools, Soft Skills, Education, Experience, Projects, Certifications), computes confidence score,
    and synchronizes extracted information into Student Profile, Projects, Certificates, and Career Profile.
    """
    template_name = 'student_portal/resume_parser.html'

    def get(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        all_resumes = list(StudentResume.objects.filter(student=student).order_by('-is_default', '-uploaded_at'))
        selected_id = request.GET.get('resume_id')

        selected_resume = None
        if selected_id:
            try:
                selected_resume = StudentResume.objects.get(pk=selected_id, student=student)
            except StudentResume.DoesNotExist:
                selected_resume = None

        if not selected_resume and all_resumes:
            selected_resume = next((r for r in all_resumes if r.is_default), all_resumes[0])

        if selected_resume and selected_resume.parser_status == 'PENDING':
            parse_resume_file(selected_resume)

        prog_langs = []
        tools = []
        soft_skills = []
        all_skills = []
        education = []
        experience = []
        projects = []
        certificates = []

        if selected_resume:
            prog_langs = json.loads(selected_resume.programming_languages_found or '[]')
            tools = json.loads(selected_resume.tools_found or '[]')
            soft_skills = json.loads(selected_resume.soft_skills_found or '[]')
            all_skills = json.loads(selected_resume.skills_found or '[]')
            education = json.loads(selected_resume.education_found or '[]')
            experience = json.loads(selected_resume.experience_found or '[]')
            projects = json.loads(selected_resume.projects_found or '[]')
            certificates = json.loads(selected_resume.certificates_found or '[]')

        return render(request, self.template_name, {
            **_base_ctx(request, student),
            'all_resumes': all_resumes,
            'selected_resume': selected_resume,
            'prog_langs': prog_langs,
            'tools': tools,
            'soft_skills': soft_skills,
            'all_skills': all_skills,
            'education': education,
            'experience': experience,
            'projects': projects,
            'certificates': certificates,
        })

    def post(self, request, *args, **kwargs):
        student = _get_student(request)
        if not student:
            return redirect('accounts:logout')

        resume_id = request.POST.get('resume_id')
        selected_resume = get_object_or_404(StudentResume, pk=resume_id, student=student)

        # 1. Execute AI Parser
        parse_resume_file(selected_resume)

        # 2. Sync to Profile
        sync_res = sync_extracted_data_to_profile(student, selected_resume)

        messages.success(
            request,
            f"AI Resume Parsing completed! Synced {sync_res['skills_added']} skills, "
            f"{sync_res['projects_synced']} projects, and {sync_res['certificates_synced']} certificates to your Student Profile."
        )

        from django.urls import reverse
        return redirect(f"{reverse('student_portal:resume_parser')}?resume_id={selected_resume.pk}")



