import io
import csv
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from colleges.models import College
from departments.models import Department
from batches.models import Batch
from students.models import Student

User = get_user_model()

class StudentImportTestCase(TestCase):
    def setUp(self):
        # Create college
        self.college = College.objects.create(
            name="Test Institute of Technology",
            code="TIT",
            website="https://tit.edu"
        )
        
        # Create college admin user
        self.admin_user = User.objects.create_user(
            username="tit_admin",
            email="admin@tit.edu",
            password="adminpassword123",
            role=User.Role.COLLEGE_ADMIN,
            college=self.college
        )
        
        # Create department
        self.department = Department.objects.create(
            college=self.college,
            name="Computer Science and Engineering",
            code="CSE"
        )
        
        # Create batch
        self.batch = Batch.objects.create(
            department=self.department,
            name="2027 CSE",
            graduation_year=2027
        )
        
        # Log in admin user
        self.client = Client()
        self.client.login(username="tit_admin", password="adminpassword123")
        
        self.import_url = reverse('batches:import_students', kwargs={'pk': self.batch.pk})
        self.preview_url = reverse('batches:import_preview', kwargs={'pk': self.batch.pk})
        self.report_url = reverse('batches:import_report', kwargs={'pk': self.batch.pk})

    def generate_csv_file(self, headers, rows):
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
        csv_buffer.seek(0)
        # Create a file-like object Django can handle
        file_obj = io.BytesIO(csv_buffer.getvalue().encode('utf-8'))
        file_obj.name = 'students.csv'
        return file_obj

    def test_import_workflow_success(self):
        # Generate valid CSV file
        csv_file = self.generate_csv_file(
            ['roll_number', 'name', 'email', 'phone'],
            [
                ['TIT-2027-001', 'John Doe', 'john.doe@tit.edu', '9876543210'],
                ['TIT-2027-002', 'Jane Smith', 'jane.smith@tit.edu', ''],
                ['', '', '', ''], # completely empty row to be skipped
                ['TIT-2027-003', 'Bob Johnson', 'bob.johnson@tit.edu', '9876543212']
            ]
        )
        
        # 1. Post to import view
        response = self.client.post(self.import_url, {
            'default_password': 'StudentDefaultPassword123',
            'csv_file': csv_file
        })
        
        # Should redirect to preview URL
        self.assertRedirects(response, self.preview_url)
        
        # Verify session variables are set
        preview_data = self.client.session.get('import_preview_data')
        self.assertEqual(len(preview_data), 3) # should skip the empty row
        self.assertEqual(preview_data[0]['roll_number'], 'TIT-2027-001')
        self.assertEqual(preview_data[1]['roll_number'], 'TIT-2027-002')
        self.assertEqual(preview_data[2]['roll_number'], 'TIT-2027-003')
        
        self.assertEqual(self.client.session.get('import_default_password'), 'StudentDefaultPassword123')

        # 2. Get the Preview Page
        preview_response = self.client.get(self.preview_url)
        self.assertEqual(preview_response.status_code, 200)
        self.assertContains(preview_response, 'John Doe')
        self.assertContains(preview_response, 'Jane Smith')
        self.assertContains(preview_response, 'Bob Johnson')

        # 3. Confirm & Import (POST to preview page)
        confirm_response = self.client.post(self.preview_url)
        self.assertEqual(confirm_response.status_code, 302)
        self.assertTrue(confirm_response['Location'].endswith(self.report_url))

        # 4. Verify created accounts and profiles
        self.assertEqual(User.objects.filter(role=User.Role.STUDENT).count(), 3)
        self.assertEqual(Student.objects.filter(college=self.college, batch=self.batch).count(), 3)

        # Verify details of a specific imported student
        student_user = User.objects.get(username='TIT-2027-001')
        self.assertEqual(student_user.email, 'john.doe@tit.edu')
        self.assertTrue(student_user.must_change_password)
        self.assertTrue(student_user.check_password('StudentDefaultPassword123'))
        
        student_profile = student_user.student_profile
        self.assertEqual(student_profile.name, 'John Doe')
        self.assertEqual(student_profile.roll_number, 'TIT-2027-001')
        self.assertEqual(student_profile.email, 'john.doe@tit.edu')
        self.assertEqual(student_profile.phone, '9876543210')
        self.assertEqual(student_profile.college, self.college)
        self.assertEqual(student_profile.department, self.department)
        self.assertEqual(student_profile.batch, self.batch)

        # 5. Get Report Page
        report_response = self.client.get(self.report_url)
        self.assertEqual(report_response.status_code, 200)
        self.assertContains(report_response, 'Import Completed Successfully!')
        self.assertContains(report_response, 'TIT-2027-001')

        # Verify session is cleaned up after accessing report page
        report_response = self.client.get(self.report_url)
        self.assertRedirects(report_response, reverse('batches:dashboard', kwargs={'pk': self.batch.pk}))

    def test_import_missing_columns(self):
        csv_file = self.generate_csv_file(
            ['roll_number', 'name', 'phone'], # missing 'email'
            [
                ['TIT-2027-001', 'John Doe', '9876543210']
            ]
        )
        response = self.client.post(self.import_url, {
            'default_password': 'StudentDefaultPassword123',
            'csv_file': csv_file
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CSV is missing required columns")

    def test_import_invalid_email(self):
        csv_file = self.generate_csv_file(
            ['roll_number', 'name', 'email', 'phone'],
            [
                ['TIT-2027-001', 'John Doe', 'invalid_email_format', '9876543210']
            ]
        )
        response = self.client.post(self.import_url, {
            'default_password': 'StudentDefaultPassword123',
            'csv_file': csv_file
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email &#x27;invalid_email_format&#x27; is invalid.")

    def test_import_duplicate_in_csv(self):
        csv_file = self.generate_csv_file(
            ['roll_number', 'name', 'email', 'phone'],
            [
                ['TIT-2027-001', 'John Doe', 'john.doe@tit.edu', ''],
                ['tit-2027-001', 'John Smith', 'john.smith@tit.edu', ''], # Duplicate Roll Number (case-insensitive)
                ['TIT-2027-002', 'Jane Smith', 'JOHN.DOE@TIT.EDU', '']    # Duplicate Email (case-insensitive)
            ]
        )
        response = self.client.post(self.import_url, {
            'default_password': 'StudentDefaultPassword123',
            'csv_file': csv_file
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Duplicate Roll Number &#x27;tit-2027-001&#x27; within CSV.")
        self.assertContains(response, "Duplicate Email &#x27;JOHN.DOE@TIT.EDU&#x27; within CSV.")

    def test_import_database_collisions(self):
        # Pre-populate database with an existing User and Student
        existing_user = User.objects.create_user(
            username="TIT-2027-X01",
            email="existing@tit.edu",
            password="somepassword"
        )
        
        # Create student profile
        Student.objects.create(
            user=existing_user,
            college=self.college,
            department=self.department,
            batch=self.batch,
            roll_number="TIT-2027-COLLISION",
            name="Existing Student",
            email="existing@tit.edu"
        )

        # Create other user globally with same email/username to trigger collisions
        other_college = College.objects.create(name="Other College", code="OC")
        other_user = User.objects.create_user(
            username="GLOBAL-COLLISION",
            email="global@tit.edu",
            password="password",
            college=other_college
        )

        csv_file = self.generate_csv_file(
            ['roll_number', 'name', 'email', 'phone'],
            [
                ['tit-2027-collision', 'Collision Roll', 'fresh1@tit.edu', ''], # Roll number collision in college
                ['TIT-2027-X01', 'Collision Username', 'fresh2@tit.edu', ''],  # Username collision in system
                ['TIT-2027-001', 'Collision Email', 'GLOBAL@tit.edu', '']      # Email collision in system
            ]
        )
        response = self.client.post(self.import_url, {
            'default_password': 'StudentDefaultPassword123',
            'csv_file': csv_file
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already registered in your college")
        self.assertContains(response, "already registered in the system")
