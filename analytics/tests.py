from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from colleges.models import College
from students.models import Student
from departments.models import Department
from batches.models import Batch
from companies.models import Company
from placements.models import PlacementDrive, Application
from decimal import Decimal

User = get_user_model()

class AnalyticsTestCase(TestCase):
    def setUp(self):
        # Create college
        self.college = College.objects.create(
            name="Analytics University",
            code="AU",
            website="https://au.edu"
        )
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username="au_admin",
            email="admin@au.edu",
            password="adminpassword123",
            role=User.Role.COLLEGE_ADMIN,
            college=self.college
        )
        
        # Create department & batch
        self.department = Department.objects.create(college=self.college, name="Aerospace Engineering", code="ASE")
        self.batch = Batch.objects.create(department=self.department, name="Batch ASE 2026", graduation_year=2026)

        # Create student profile
        self.student = Student.objects.create(
            college=self.college,
            department=self.department,
            batch=self.batch,
            roll_number="ASE001",
            name="Jane Doe",
            email="jane@au.edu",
            cgpa=Decimal("9.50"),
            backlogs=0,
            placement_status=Student.PlacementStatus.PLACED,
            package_amount=Decimal("15.50")
        )

        # Create company
        self.company = Company.objects.create(
            college=self.college,
            name="Boeing Inc",
            website="https://boeing.com",
            location="Seattle"
        )

        # Create placement drive
        self.drive = PlacementDrive.objects.create(
            college=self.college,
            company=self.company,
            role="Aerospace Designer",
            drive_type=PlacementDrive.DriveType.JOB,
            package_amount=Decimal("15.50"),
            status=PlacementDrive.Status.ACTIVE
        )
        
        # Create student user and application selection
        self.student_user = User.objects.create_user(
            username="jane_stud",
            email="jane@au.edu",
            password="studpassword123",
            role=User.Role.STUDENT,
            college=self.college
        )
        self.student.user = self.student_user
        self.student.save()
        
        self.application = Application.objects.create(
            drive=self.drive,
            student=self.student,
            status=Application.ApplicationStatus.SELECTED
        )

        self.client = Client()
        self.client.login(username="au_admin", password="adminpassword123")

        self.dashboard_url = reverse('analytics:dashboard')

    def test_analytics_dashboard_rendering(self):
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        
        # Check Core KPIs are rendered
        self.assertContains(response, "100.0%")  # Placement ratio
        self.assertContains(response, "15.50 LPA")  # Highest/Avg package
        
        # Check charts context variables
        self.assertIn('status_chart', response.context)
        self.assertIn('dept_chart', response.context)
        self.assertIn('batch_chart', response.context)
        self.assertIn('student_chart', response.context)
        self.assertIn('company_chart', response.context)
        
        # Check that base64 encoded image strings are present in output html
        self.assertContains(response, "data:image/png;base64,")
        self.assertContains(response, "Boeing Inc")
