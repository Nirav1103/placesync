import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.contrib.auth import get_user_model

from students.models import Student
from departments.models import Department
from batches.models import Batch
from .forms import StudentEditForm, StudentMoveForm, StudentResetPasswordForm

User = get_user_model()

class StudentListView(LoginRequiredMixin, View):
    template_name = 'students/student_list.html'

    def get(self, request, *args, **kwargs):
        if hasattr(request.user, 'role') and request.user.role == 'STUDENT':
            messages.warning(request, "Access restricted to College Admin staff.")
            return redirect('student_portal:dashboard')

        college = request.user.college
        if not college:
            raise Http404("No college associated with your account.")

        students = Student.objects.filter(college=college).select_related('user', 'department', 'batch')

        # Extract filter parameters
        dept_id = request.GET.get('department', '').strip()
        batch_id = request.GET.get('batch', '').strip()
        cgpa_filter = request.GET.get('cgpa', '').strip()
        status_filter = request.GET.get('placement_status', '').strip()
        q = request.GET.get('q', '').strip()

        # Apply Search
        if q:
            students = students.filter(
                Q(name__icontains=q) | 
                Q(roll_number__icontains=q) | 
                Q(email__icontains=q)
            )

        # Apply Filters
        if dept_id:
            students = students.filter(department_id=dept_id)
        if batch_id:
            students = students.filter(batch_id=batch_id)
        if status_filter:
            students = students.filter(placement_status=status_filter)
        if cgpa_filter:
            try:
                cgpa_val = float(cgpa_filter)
                students = students.filter(cgpa__gte=cgpa_val)
            except ValueError:
                pass

        # Sort
        students = students.order_by('roll_number')

        # Dropdowns data
        departments = Department.objects.filter(college=college).order_by('name')
        batches = Batch.objects.filter(department__college=college).order_by('-graduation_year', 'name')
        placement_statuses = Student.PlacementStatus.choices

        context = {
            'students': students,
            'departments': departments,
            'batches': batches,
            'placement_statuses': placement_statuses,
            'selected_dept': dept_id,
            'selected_batch': batch_id,
            'selected_cgpa': cgpa_filter,
            'selected_status': status_filter,
            'q': q
        }
        return render(request, self.template_name, context)


class StudentEditView(LoginRequiredMixin, View):
    template_name = 'students/student_form.html'
    form_class = StudentEditForm

    def get(self, request, pk, *args, **kwargs):
        student = get_object_or_404(Student, pk=pk, college=request.user.college)
        form = self.form_class(instance=student, college=request.user.college)
        return render(request, self.template_name, {'form': form, 'student': student})

    def post(self, request, pk, *args, **kwargs):
        student = get_object_or_404(Student, pk=pk, college=request.user.college)
        form = self.form_class(request.POST, instance=student, college=request.user.college)
        if form.is_valid():
            form.save()
            messages.success(request, f"Student '{student.name}' profile details have been saved.")
            return redirect('students:list')
        return render(request, self.template_name, {'form': form, 'student': student})


class StudentDeleteView(LoginRequiredMixin, View):
    template_name = 'students/student_confirm_delete.html'

    def get(self, request, pk, *args, **kwargs):
        student = get_object_or_404(Student, pk=pk, college=request.user.college)
        return render(request, self.template_name, {'student': student})

    def post(self, request, pk, *args, **kwargs):
        student = get_object_or_404(Student, pk=pk, college=request.user.college)
        name = student.name
        
        # Delete user account first if it exists
        if student.user:
            student.user.delete()
        else:
            student.delete()
            
        messages.success(request, f"Student '{name}' has been deleted successfully from the system.")
        return redirect('students:list')


class StudentSuspendView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        student = get_object_or_404(Student, pk=pk, college=request.user.college)
        if not student.user:
            messages.error(request, f"No user account linked with student '{student.name}' to toggle status.")
            return redirect('students:list')

        # Toggle is_active status of linked User
        user = student.user
        user.is_active = not user.is_active
        user.save()

        status_str = "suspended" if not user.is_active else "reactivated"
        messages.success(request, f"Student '{student.name}' account has been {status_str}.")
        return redirect('students:list')


class StudentResetPasswordView(LoginRequiredMixin, View):
    template_name = 'students/student_reset_password.html'
    form_class = StudentResetPasswordForm

    def get(self, request, pk, *args, **kwargs):
        student = get_object_or_404(Student, pk=pk, college=request.user.college)
        form = self.form_class()
        return render(request, self.template_name, {'form': form, 'student': student})

    def post(self, request, pk, *args, **kwargs):
        student = get_object_or_404(Student, pk=pk, college=request.user.college)
        form = self.form_class(request.POST)
        if form.is_valid():
            if not student.user:
                messages.error(request, f"No login account is associated with '{student.name}'.")
                return redirect('students:list')
                
            password = form.cleaned_data['password']
            user = student.user
            user.set_password(password)
            user.must_change_password = True # Enforce change on next login
            user.save()
            
            messages.success(request, f"Password reset successfully for student '{student.name}'. They must change it on their next login.")
            return redirect('students:list')
        return render(request, self.template_name, {'form': form, 'student': student})


class StudentMoveView(LoginRequiredMixin, View):
    template_name = 'students/student_move.html'
    form_class = StudentMoveForm

    def get(self, request, pk, *args, **kwargs):
        student = get_object_or_404(Student, pk=pk, college=request.user.college)
        form = self.form_class(college=request.user.college, initial={'batch': student.batch})
        return render(request, self.template_name, {'form': form, 'student': student})

    def post(self, request, pk, *args, **kwargs):
        student = get_object_or_404(Student, pk=pk, college=request.user.college)
        form = self.form_class(request.POST, college=request.user.college)
        if form.is_valid():
            target_batch = form.cleaned_data['batch']
            
            # Transfer student to the new batch and department
            student.batch = target_batch
            student.department = target_batch.department
            student.save()
            
            messages.success(request, f"Student '{student.name}' has been moved to batch '{target_batch.name}' ({target_batch.department.code}).")
            return redirect('students:list')
        return render(request, self.template_name, {'form': form, 'student': student})


class StudentExportView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        college = request.user.college
        if not college:
            raise Http404("No college associated with your account.")

        students = Student.objects.filter(college=college).select_related('department', 'batch')

        # Apply same filter criteria as ListView to export correct selection
        dept_id = request.GET.get('department', '').strip()
        batch_id = request.GET.get('batch', '').strip()
        cgpa_filter = request.GET.get('cgpa', '').strip()
        status_filter = request.GET.get('placement_status', '').strip()
        q = request.GET.get('q', '').strip()

        if q:
            students = students.filter(
                Q(name__icontains=q) | 
                Q(roll_number__icontains=q) | 
                Q(email__icontains=q)
            )
        if dept_id:
            students = students.filter(department_id=dept_id)
        if batch_id:
            students = students.filter(batch_id=batch_id)
        if status_filter:
            students = students.filter(placement_status=status_filter)
        if cgpa_filter:
            try:
                cgpa_val = float(cgpa_filter)
                students = students.filter(cgpa__gte=cgpa_val)
            except ValueError:
                pass

        students = students.order_by('roll_number')

        # CSV response initialization
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="students_list.csv"'

        writer = csv.writer(response)
        # Write CSV Header
        writer.writerow([
            'Roll Number', 
            'Student Name', 
            'Email Address', 
            'Phone Number', 
            'Department Code', 
            'Department Name', 
            'Batch Name', 
            'Placement Status', 
            'CGPA', 
            'Package Amount (LPA)', 
            'Stipend Amount'
        ])

        # Write CSV rows
        for s in students:
            writer.writerow([
                s.roll_number,
                s.name,
                s.email,
                s.phone,
                s.department.code,
                s.department.name,
                s.batch.name,
                s.get_placement_status_display(),
                s.cgpa,
                s.package_amount or '-',
                s.stipend_amount or '-'
            ])

        return response
