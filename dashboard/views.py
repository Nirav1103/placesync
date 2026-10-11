from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.db.models import Avg, Max

from students.models import Student
from departments.models import Department
from batches.models import Batch
from companies.models import Company
from placements.models import PlacementDrive, Application
from communication.models import Notification


class DashboardIndexView(LoginRequiredMixin, View):
    template_name = 'dashboard/index.html'

    def get(self, request, *args, **kwargs):
        # 1. Role Redirect: If user is a student, redirect to student portal dashboard
        if hasattr(request.user, 'role') and request.user.role == 'STUDENT':
            return redirect('student_portal:dashboard')

        college = getattr(request.user, 'college', None)
        stats = {}
        upcoming_drives = []
        latest_applications = []

        if college:
            # Total Students
            total_students = Student.objects.filter(college=college).count()
            stats['total_students'] = total_students

            # Total Departments
            stats['total_departments'] = Department.objects.filter(college=college).count()

            # Total Batches
            stats['total_batches'] = Batch.objects.filter(department__college=college).count()

            # Total Companies
            stats['total_companies'] = Company.objects.filter(college=college).count()

            # Active Placement Drives
            stats['active_drives'] = PlacementDrive.objects.filter(college=college, status='ACTIVE').count()

            # Placed & Internship counts
            placed_students = Student.objects.filter(
                college=college,
                placement_status__in=['PLACED', 'PLACED_AND_INTERN']
            ).count()
            stats['placed_students'] = placed_students

            internship_students = Student.objects.filter(
                college=college,
                placement_status__in=['INTERN', 'PLACED_AND_INTERN']
            ).count()
            stats['internship_students'] = internship_students

            # Placement Percentage
            stats['placement_ratio'] = round((placed_students / total_students * 100), 1) if total_students > 0 else 0.0

            # Salary packages (LPA)
            placed_qs = Student.objects.filter(college=college, placement_status__in=['PLACED', 'PLACED_AND_INTERN'])
            stats['highest_package'] = round(placed_qs.aggregate(Max('package_amount'))['package_amount__max'] or 0.0, 2)
            stats['average_package'] = round(placed_qs.aggregate(Avg('package_amount'))['package_amount__avg'] or 0.0, 2)

            # Stipends
            intern_qs = Student.objects.filter(college=college, placement_status__in=['INTERN', 'PLACED_AND_INTERN'])
            stats['highest_stipend'] = round(intern_qs.aggregate(Max('stipend_amount'))['stipend_amount__max'] or 0.0, 2)
            stats['average_stipend'] = round(intern_qs.aggregate(Avg('stipend_amount'))['stipend_amount__avg'] or 0.0, 2)

            # Pending Notifications (for the logged in College Admin user)
            stats['unread_notifications'] = Notification.objects.filter(user=request.user, is_read=False).count()

            # Upcoming Drives (drives with status UPCOMING)
            upcoming_drives = PlacementDrive.objects.filter(
                college=college,
                status='UPCOMING'
            ).select_related('company').order_by('-created_at')[:5]

            # Latest Applications
            latest_applications = Application.objects.filter(
                drive__college=college
            ).select_related('drive', 'drive__company', 'student').order_by('-applied_at')[:5]

        else:
            stats = {
                'total_students': 0,
                'total_departments': 0,
                'total_batches': 0,
                'total_companies': 0,
                'active_drives': 0,
                'placed_students': 0,
                'internship_students': 0,
                'placement_ratio': 0.0,
                'highest_package': 0.0,
                'average_package': 0.0,
                'highest_stipend': 0.0,
                'average_stipend': 0.0,
                'unread_notifications': 0,
            }

        context = {
            'stats': stats,
            'upcoming_drives': upcoming_drives,
            'latest_applications': latest_applications,
        }
        return render(request, self.template_name, context)
