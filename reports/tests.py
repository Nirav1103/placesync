from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from colleges.models import College
from students.models import Student
from departments.models import Department
from batches.models import Batch
from companies.models import Company
from placements.models import PlacementDrive
from decimal import Decimal

User = get_user_model()

class ReportsTestCase(TestCase):
    def setUp(self):
        # Create college
        self.college = College.objects.create(
            name="Reports University",
            code="RU",
            website="https://ru.edu"
        )
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username="ru_admin",
            email="admin@ru.edu",
            password="adminpassword123",
            role=User.Role.COLLEGE_ADMIN,
            college=self.college
        )
        
        # Create department & batch
        self.department = Department.objects.create(college=self.college, name="Computer Science", code="CSE")
        self.batch = Batch.objects.create(department=self.department, name="Batch 2026", graduation_year=2026)

        # Create students
        self.student = Student.objects.create(
            college=self.college,
            department=self.department,
            batch=self.batch,
            roll_number="CSE100",
            name="John Doe",
            email="john@ru.edu",
            cgpa=Decimal("9.00"),
            backlogs=0,
            placement_status=Student.PlacementStatus.PLACED,
            package_amount=Decimal("12.50")
        )

        # Create company
        self.company = Company.objects.create(
            college=self.college,
            name="Google Inc",
            website="https://google.com",
            location="Bangalore"
        )

        # Create placement drive
        self.drive = PlacementDrive.objects.create(
            college=self.college,
            company=self.company,
            role="Systems Engineer",
            drive_type=PlacementDrive.DriveType.JOB,
            package_amount=Decimal("12.50"),
            status=PlacementDrive.Status.ACTIVE
        )

        self.client = Client()
        self.client.login(username="ru_admin", password="adminpassword123")

        self.dashboard_url = reverse('reports:dashboard')

    def test_reports_dashboard(self):
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Overall Placement Report")
        self.assertContains(response, "Salary Distribution Report")

    def test_view_report_pages(self):
        reports = ['placement', 'student', 'batch', 'company', 'salary', 'internship']
        for r in reports:
            view_url = reverse('reports:view_report', kwargs={'report_type': r})
            response = self.client.get(view_url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Export CSV")
            self.assertContains(response, "Export PDF")

    def test_export_reports_csv(self):
        reports = ['placement', 'student', 'batch', 'company', 'salary', 'internship']
        for r in reports:
            export_url = reverse('reports:export_report', kwargs={'report_type': r, 'export_format': 'csv'})
            response = self.client.get(export_url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'text/csv')
            self.assertIn(f'attachment; filename="{r}_report.csv"', response['Content-Disposition'])
            # Verify body contains data
            body_content = response.content.decode('utf-8')
            self.assertTrue(len(body_content) > 0)

    def test_export_reports_pdf(self):
        reports = ['placement', 'student', 'batch', 'company', 'salary', 'internship']
        for r in reports:
            export_url = reverse('reports:export_report', kwargs={'report_type': r, 'export_format': 'pdf'})
            response = self.client.get(export_url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/pdf')
            self.assertIn(f'attachment; filename="{r}_report.pdf"', response['Content-Disposition'])
            # Verify PDF starts with standard PDF magic header
            self.assertTrue(b"".join(response.streaming_content).startswith(b'%PDF'))
