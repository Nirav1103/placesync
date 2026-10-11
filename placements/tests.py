from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from colleges.models import College
from companies.models import Company
from departments.models import Department
from batches.models import Batch
from students.models import Student
from placements.models import PlacementDrive, Application

User = get_user_model()

class PlacementDriveTestCase(TestCase):
    def setUp(self):
        # Create college
        self.college = College.objects.create(
            name="Test University",
            code="TU",
            website="https://tu.edu"
        )
        
        # Create departments
        self.dept_cse = Department.objects.create(college=self.college, name="Computer Science", code="CSE")
        self.dept_ece = Department.objects.create(college=self.college, name="Electronics", code="ECE")
        
        # Create batch
        self.batch = Batch.objects.create(department=self.dept_cse, name="2026 Batch", graduation_year=2026)

        # Create admin user
        self.admin_user = User.objects.create_user(
            username="tu_admin",
            email="admin@tu.edu",
            password="adminpassword123",
            role=User.Role.COLLEGE_ADMIN,
            college=self.college
        )
        
        # Create student user 1 (CSE, CGPA 8.50, 0 Backlogs)
        self.student_user_1 = User.objects.create_user(
            username="stud_1",
            email="stud1@tu.edu",
            password="studpassword123",
            role=User.Role.STUDENT,
            college=self.college
        )
        self.student_1 = Student.objects.create(
            user=self.student_user_1,
            college=self.college,
            department=self.dept_cse,
            batch=self.batch,
            roll_number="CSE001",
            name="Student CSE One",
            email="stud1@tu.edu",
            cgpa=Decimal("8.50"),
            backlogs=0
        )

        # Create student user 2 (ECE, CGPA 7.20, 2 Backlogs)
        self.student_user_2 = User.objects.create_user(
            username="stud_2",
            email="stud2@tu.edu",
            password="studpassword123",
            role=User.Role.STUDENT,
            college=self.college
        )
        self.student_2 = Student.objects.create(
            user=self.student_user_2,
            college=self.college,
            department=self.dept_ece,
            batch=self.batch,
            roll_number="ECE001",
            name="Student ECE Two",
            email="stud2@tu.edu",
            cgpa=Decimal("7.20"),
            backlogs=2
        )

        # Create company
        self.company = Company.objects.create(
            college=self.college,
            name="TechCorp",
            website="https://techcorp.com",
            location="San Jose, CA"
        )

        # Create active drive (CSE only, CGPA >= 8.00, Backlogs <= 0)
        self.job_drive = PlacementDrive.objects.create(
            college=self.college,
            company=self.company,
            role="Software Engineer",
            drive_type=PlacementDrive.DriveType.JOB,
            package_amount=Decimal("15.00"),
            job_mode="ON_SITE",
            deadline=timezone.localdate() + timedelta(days=5),
            min_cgpa=Decimal("8.00"),
            max_backlogs=0,
            status=PlacementDrive.Status.ACTIVE,
            selection_process="Online coding assessment followed by technical interviews."
        )
        self.job_drive.eligible_departments.add(self.dept_cse)

        # Create expired drive
        self.expired_drive = PlacementDrive.objects.create(
            college=self.college,
            company=self.company,
            role="Intern Web Developer",
            drive_type=PlacementDrive.DriveType.INTERNSHIP,
            package_amount=Decimal("30000.00"),
            job_mode="REMOTE",
            deadline=timezone.localdate() - timedelta(days=2),
            min_cgpa=Decimal("6.00"),
            max_backlogs=1,
            status=PlacementDrive.Status.ACTIVE
        )

        self.client = Client()

    def test_admin_view_drives_and_stats(self):
        self.client.login(username="tu_admin", password="adminpassword123")
        
        list_url = reverse('placements:list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        
        # Verify stats calculations
        self.assertEqual(response.context['total_count'], 2)
        self.assertEqual(response.context['active_count'], 2)
        self.assertEqual(response.context['jobs_count'], 1)
        self.assertEqual(response.context['internships_count'], 1)

    def test_student_eligible_drives_listing(self):
        # Log in student 1 (CSE, CGPA 8.50, 0 Backlogs - Eligible for Software Engineer)
        self.client.login(username="stud_1", password="studpassword123")
        
        list_url = reverse('placements:list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        
        # Verify student listing data
        drives_in_context = response.context['drives']
        
        # Software Engineer item check
        swe_item = next(item for item in drives_in_context if item['drive'].role == "Software Engineer")
        self.assertTrue(swe_item['is_eligible'])
        self.assertFalse(swe_item['already_applied'])

        # Intern Web Developer item check (Expired deadline)
        intern_item = next(item for item in drives_in_context if item['drive'].role == "Intern Web Developer")
        self.assertFalse(intern_item['is_eligible'])
        self.assertIn("Deadline", intern_item['reasons'][0])

    def test_student_apply_flow_success_and_failure(self):
        # 1. Successful application (Student 1 meets all CSE drive requirements)
        self.client.login(username="stud_1", password="studpassword123")
        detail_url = reverse('placements:detail', kwargs={'pk': self.job_drive.pk})
        apply_url = reverse('placements:apply', kwargs={'pk': self.job_drive.pk})
        
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Submit Application")

        response = self.client.post(apply_url)
        self.assertRedirects(response, detail_url)
        self.assertTrue(Application.objects.filter(drive=self.job_drive, student=self.student_1).exists())

        # 2. Blocked application (Student 2 fails CGPA, backlogs, and department requirements)
        self.client.login(username="stud_2", password="studpassword123")
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Submit Application")
        self.assertContains(response, "Application Blocked")

        # Try to force POST application
        response = self.client.post(apply_url)
        self.assertRedirects(response, detail_url)
        self.assertFalse(Application.objects.filter(drive=self.job_drive, student=self.student_2).exists())

    def test_admin_update_application_status(self):
        # Create application for student 1
        application = Application.objects.create(
            drive=self.job_drive,
            student=self.student_1,
            status=Application.ApplicationStatus.APPLIED
        )
        
        # Log in Admin
        self.client.login(username="tu_admin", password="adminpassword123")
        detail_url = reverse('placements:detail', kwargs={'pk': self.job_drive.pk})
        
        # Load drive details and check application listed
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Student CSE One")
        self.assertContains(response, "CSE001")

        # Update application status to Shortlisted
        status_url = reverse('placements:update_status', kwargs={'app_pk': application.pk, 'new_status': 'SHORTLISTED'})
        response = self.client.post(status_url)
        self.assertRedirects(response, detail_url)
        
        application.refresh_from_db()
        self.assertEqual(application.status, Application.ApplicationStatus.SHORTLISTED)

        # Update application status to Selected
        status_url = reverse('placements:update_status', kwargs={'app_pk': application.pk, 'new_status': 'SELECTED'})
        response = self.client.post(status_url)
        self.assertRedirects(response, detail_url)
        
        application.refresh_from_db()
        self.assertEqual(application.status, Application.ApplicationStatus.SELECTED)
