from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import Http404, HttpResponseForbidden
from django.urls import reverse
from django.utils import timezone

from .models import PlacementDrive, Application
from .forms import PlacementDriveForm, StudentApplyForm
from students.models import Student

class PlacementDriveListView(LoginRequiredMixin, View):
    template_name = 'placements/drive_list.html'

    def get(self, request, *args, **kwargs):
        college = request.user.college
        if not college:
            raise Http404("No college associated with your account.")

        if request.user.role == 'COLLEGE_ADMIN':
            drives = PlacementDrive.objects.filter(college=college).select_related('company')
            
            total_count = drives.count()
            active_count = drives.filter(status='ACTIVE').count()
            jobs_count = drives.filter(drive_type='JOB').count()
            internships_count = drives.filter(drive_type='INTERNSHIP').count()
            
            q = request.GET.get('q', '').strip()
            if q:
                drives = drives.filter(role__icontains=q) | drives.filter(company__name__icontains=q)

            context = {
                'is_admin': True,
                'drives': drives,
                'q': q,
                'total_count': total_count,
                'active_count': active_count,
                'jobs_count': jobs_count,
                'internships_count': internships_count
            }
            return render(request, self.template_name, context)
            
        elif request.user.role == 'STUDENT':
            student = get_object_or_404(Student, user=request.user, college=college)
            
            # Get active drives
            drives = PlacementDrive.objects.filter(college=college, status='ACTIVE').select_related('company')
            
            # Fetch student's own applications
            my_applications = Application.objects.filter(student=student).select_related('drive', 'drive__company')
            applied_drive_ids = [app.drive_id for app in my_applications]
            
            # Process eligibility annotations
            annotated_drives = []
            for drive in drives:
                eligible = True
                reasons = []
                
                # Check department
                if drive.eligible_departments.exists() and student.department not in drive.eligible_departments.all():
                    eligible = False
                    reasons.append(f"Department ({student.department.code}) not eligible")
                    
                # Check CGPA
                if student.cgpa is not None and student.cgpa < drive.min_cgpa:
                    eligible = False
                    reasons.append(f"CGPA is {student.cgpa}, minimum required is {drive.min_cgpa}")
                elif student.cgpa is None and drive.min_cgpa > 0:
                    eligible = False
                    reasons.append(f"CGPA is not specified, minimum required is {drive.min_cgpa}")
                    
                # Check Backlogs
                if student.backlogs > drive.max_backlogs:
                    eligible = False
                    reasons.append(f"Backlogs is {student.backlogs}, maximum allowed is {drive.max_backlogs}")
                    
                # Check Deadline
                if drive.deadline and timezone.localdate() > drive.deadline:
                    eligible = False
                    reasons.append(f"Deadline ({drive.deadline}) has passed")

                already_applied = drive.id in applied_drive_ids
                
                annotated_drives.append({
                    'drive': drive,
                    'is_eligible': eligible,
                    'reasons': reasons,
                    'already_applied': already_applied
                })
                
            context = {
                'is_admin': False,
                'drives': annotated_drives,
                'my_applications': my_applications
            }
            return render(request, self.template_name, context)
            
        else:
            raise Http404("Invalid role.")

class PlacementDriveCreateView(LoginRequiredMixin, View):
    template_name = 'placements/drive_form.html'
    form_class = PlacementDriveForm

    def get(self, request, *args, **kwargs):
        if request.user.role != 'COLLEGE_ADMIN':
            return HttpResponseForbidden("Only college admins can launch drives.")
        form = self.form_class(college=request.user.college)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        if request.user.role != 'COLLEGE_ADMIN':
            return HttpResponseForbidden("Only college admins can launch drives.")
        form = self.form_class(request.POST, college=request.user.college)
        if form.is_valid():
            drive = form.save(commit=False)
            drive.college = request.user.college
            drive.save()
            form.save_m2m()
            messages.success(request, f"Placement Drive for '{drive.role}' at {drive.company.name} launched successfully.")
            return redirect('placements:list')
        return render(request, self.template_name, {'form': form})

class PlacementDriveDetailView(LoginRequiredMixin, View):
    template_name = 'placements/drive_detail.html'

    def get(self, request, pk, *args, **kwargs):
        college = request.user.college
        drive = get_object_or_404(PlacementDrive, pk=pk, college=college)
        
        if request.user.role == 'COLLEGE_ADMIN':
            applications = drive.applications.select_related('student', 'student__department').order_by('applied_at')
            context = {
                'is_admin': True,
                'drive': drive,
                'applications': applications
            }
            return render(request, self.template_name, context)
            
        elif request.user.role == 'STUDENT':
            student = get_object_or_404(Student, user=request.user, college=college)
            
            # Check eligibility criteria details
            is_eligible = True
            reasons = []
            
            # Department checklist
            dept_ok = True
            if drive.eligible_departments.exists() and student.department not in drive.eligible_departments.all():
                is_eligible = False
                dept_ok = False
                reasons.append(f"Your department ({student.department.code}) is not eligible for this drive.")
                
            # CGPA checklist
            cgpa_ok = True
            if student.cgpa is not None and student.cgpa < drive.min_cgpa:
                is_eligible = False
                cgpa_ok = False
                reasons.append(f"Your CGPA is {student.cgpa}, below the required minimum of {drive.min_cgpa}.")
            elif student.cgpa is None and drive.min_cgpa > 0:
                is_eligible = False
                cgpa_ok = False
                reasons.append(f"Your CGPA is not set, below the required minimum of {drive.min_cgpa}.")
                
            # Backlog checklist
            backlogs_ok = True
            if student.backlogs > drive.max_backlogs:
                is_eligible = False
                backlogs_ok = False
                reasons.append(f"You have {student.backlogs} active backlogs, which exceeds the limit of {drive.max_backlogs}.")
                
            # Deadline checklist
            deadline_ok = True
            if drive.deadline and timezone.localdate() > drive.deadline:
                is_eligible = False
                deadline_ok = False
                reasons.append(f"The deadline ({drive.deadline}) for this application has passed.")

            application = drive.applications.filter(student=student).first()
            form = StudentApplyForm() if is_eligible and not application else None

            context = {
                'is_admin': False,
                'drive': drive,
                'is_eligible': is_eligible,
                'reasons': reasons,
                'application': application,
                'form': form,
                'dept_ok': dept_ok,
                'cgpa_ok': cgpa_ok,
                'backlogs_ok': backlogs_ok,
                'deadline_ok': deadline_ok,
                'student': student
            }
            return render(request, self.template_name, context)
        else:
            raise Http404("Invalid role.")

class StudentApplyView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        if request.user.role != 'STUDENT':
            return HttpResponseForbidden("Only students can apply to drives.")
            
        college = request.user.college
        drive = get_object_or_404(PlacementDrive, pk=pk, college=college)
        student = get_object_or_404(Student, user=request.user, college=college)

        # Validate eligibility criteria
        is_eligible = True
        reasons = []

        if drive.eligible_departments.exists() and student.department not in drive.eligible_departments.all():
            is_eligible = False
            reasons.append("Eligible departments check failed")
            
        if student.cgpa is not None and student.cgpa < drive.min_cgpa:
            is_eligible = False
            reasons.append("CGPA check failed")
        elif student.cgpa is None and drive.min_cgpa > 0:
            is_eligible = False
            reasons.append("CGPA check failed")
            
        if student.backlogs > drive.max_backlogs:
            is_eligible = False
            reasons.append("Backlogs check failed")
            
        if drive.deadline and timezone.localdate() > drive.deadline:
            is_eligible = False
            reasons.append("Deadline has passed")

        if not is_eligible:
            messages.error(request, f"Eligibility Validation Failed: {', '.join(reasons)}")
            return redirect('placements:detail', pk=drive.pk)

        # Check duplicate application
        if Application.objects.filter(drive=drive, student=student).exists():
            messages.info(request, "You have already applied for this drive.")
            return redirect('placements:detail', pk=drive.pk)

        form = StudentApplyForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.drive = drive
            application.student = student
            application.save()
            messages.success(request, f"Your application for '{drive.role}' has been submitted successfully.")
        else:
            messages.error(request, "Error submitting your resume. Please check the file and try again.")
            
        return redirect('placements:detail', pk=drive.pk)

class UpdateApplicationStatusView(LoginRequiredMixin, View):
    def post(self, request, app_pk, new_status, *args, **kwargs):
        if request.user.role != 'COLLEGE_ADMIN':
            return HttpResponseForbidden("Only administrators can update application statuses.")
            
        application = get_object_or_404(Application, pk=app_pk, drive__college=request.user.college)
        
        valid_statuses = [choice[0] for choice in Application.ApplicationStatus.choices]
        if new_status not in valid_statuses:
            messages.error(request, "Invalid status transition request.")
            return redirect('placements:detail', pk=application.drive_id)
            
        application.status = new_status
        application.save()
        messages.success(request, f"Updated application status for {application.student.name} to {application.get_status_display()}.")
        return redirect('placements:detail', pk=application.drive_id)
