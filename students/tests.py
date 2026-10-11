from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from colleges.models import College
from departments.models import Department
from batches.models import Batch
from students.models import Student

User = get_user_model()

class StudentManagementTestCase(TestCase):
    def setUp(self):
        # Create college
        self.college = College.objects.create(
            name="Test Institute of Technology",
            code="TIT",
            website="https://tit.edu"
        )
        
        # Create college admin
        self.admin_user = User.objects.create_user(
            username="tit_admin",
            email="admin@tit.edu",
            password="adminpassword123",
            role=User.Role.COLLEGE_ADMIN,
            college=self.college
        )
        
        # Create departments
        self.dept_cse = Department.objects.create(
            college=self.college,
            name="Computer Science and Engineering",
            code="CSE"
        )
        self.dept_ece = Department.objects.create(
            college=self.college,
            name="Electronics and Communication",
            code="ECE"
        )
        
        # Create batches
        self.batch_cse = Batch.objects.create(
            department=self.dept_cse,
            name="2027 CSE",
            graduation_year=2027
        )
        self.batch_ece = Batch.objects.create(
            department=self.dept_ece,
            name="2027 ECE",
            graduation_year=2027
        )

        # Create students
        self.student_user_1 = User.objects.create_user(
            username="TIT-01",
            email="student1@tit.edu",
            password="password123",
            role=User.Role.STUDENT,
            college=self.college
        )
        self.student_1 = Student.objects.create(
            user=self.student_user_1,
            college=self.college,
            department=self.dept_cse,
            batch=self.batch_cse,
            roll_number="TIT-01",
            name="Alice Cooper",
            email="student1@tit.edu",
            cgpa=9.5,
            placement_status=Student.PlacementStatus.PLACED,
            package_amount=12.0
        )

        self.student_user_2 = User.objects.create_user(
            username="TIT-02",
            email="student2@tit.edu",
            password="password123",
            role=User.Role.STUDENT,
            college=self.college
        )
        self.student_2 = Student.objects.create(
            user=self.student_user_2,
            college=self.college,
            department=self.dept_ece,
            batch=self.batch_ece,
            roll_number="TIT-02",
            name="Bob Miller",
            email="student2@tit.edu",
            cgpa=7.8,
            placement_status=Student.PlacementStatus.UNPLACED
        )
        
        # Log in admin client
        self.client = Client()
        self.client.login(username="tit_admin", password="adminpassword123")

        # URLs
        self.list_url = reverse('students:list')
        self.export_url = reverse('students:export')

    def test_student_directory_list_and_search(self):
        # 1. View listing (both students should be listed)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice Cooper")
        self.assertContains(response, "Bob Miller")

        # 2. Search query filter
        response = self.client.get(self.list_url, {'q': 'Alice'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice Cooper")
        self.assertNotContains(response, "Bob Miller")

        # 3. Department filter
        response = self.client.get(self.list_url, {'department': self.dept_ece.pk})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Alice Cooper")
        self.assertContains(response, "Bob Miller")

        # 4. Batch filter
        response = self.client.get(self.list_url, {'batch': self.batch_cse.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice Cooper")
        self.assertNotContains(response, "Bob Miller")

        # 5. CGPA criteria filter (>= 9.0)
        response = self.client.get(self.list_url, {'cgpa': '9.0'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice Cooper")
        self.assertNotContains(response, "Bob Miller")

        # 6. Placement status filter (UNPLACED)
        response = self.client.get(self.list_url, {'placement_status': 'UNPLACED'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Alice Cooper")
        self.assertContains(response, "Bob Miller")

    def test_student_edit_success_and_failures(self):
        edit_url = reverse('students:edit', kwargs={'pk': self.student_1.pk})
        
        # 1. Load form
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice Cooper")

        # 2. Successful Edit
        response = self.client.post(edit_url, {
            'roll_number': 'TIT-01-REV',
            'name': 'Alice Cooper Revised',
            'email': 'alice.revised@tit.edu',
            'phone': '1112223333',
            'placement_status': 'PLACED',
            'package_amount': '15.0'
        })
        self.assertRedirects(response, self.list_url)
        
        # Verify db update
        self.student_1.refresh_from_db()
        self.assertEqual(self.student_1.name, 'Alice Cooper Revised')
        self.assertEqual(self.student_1.roll_number, 'TIT-01-REV')
        self.assertEqual(self.student_1.email, 'alice.revised@tit.edu')
        self.assertEqual(self.student_1.phone, '1112223333')
        
        # Verify linked User fields updated
        self.student_user_1.refresh_from_db()
        self.assertEqual(self.student_user_1.username, 'TIT-01-REV')
        self.assertEqual(self.student_user_1.email, 'alice.revised@tit.edu')

        # 3. Local College Roll Number collision
        response = self.client.post(edit_url, {
            'roll_number': 'tit-02', # case-insensitive collision with student 2
            'name': 'Alice',
            'email': 'alice.new@tit.edu',
            'placement_status': 'PLACED'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'roll_number', "A student with this roll number is already registered in this college.")

        # 4. Global Email collision
        response = self.client.post(edit_url, {
            'roll_number': 'TIT-01-REV',
            'name': 'Alice',
            'email': 'student2@tit.edu', # Collision with student 2's email
            'placement_status': 'PLACED'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'email', "This email is already registered in the system.")

        # 5. Global Username collision
        # Create an unrelated user in another college
        other_college = College.objects.create(name="Other College", code="OC")
        User.objects.create_user(username="GLOBAL-COLLIDE", email="other@oc.edu", password="pwd", college=other_college)
        
        response = self.client.post(edit_url, {
            'roll_number': 'GLOBAL-COLLIDE', # Collision with other user's username
            'name': 'Alice',
            'email': 'alice.new@tit.edu',
            'placement_status': 'PLACED'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'roll_number', "This roll number (username) is already registered in the system.")

    def test_student_move_batch(self):
        move_url = reverse('students:move', kwargs={'pk': self.student_1.pk})
        
        # Load form
        response = self.client.get(move_url)
        self.assertEqual(response.status_code, 200)
        
        # Post move to ECE batch
        response = self.client.post(move_url, {
            'batch': self.batch_ece.pk
        })
        self.assertRedirects(response, self.list_url)
        
        # Verify department and batch updated
        self.student_1.refresh_from_db()
        self.assertEqual(self.student_1.batch, self.batch_ece)
        self.assertEqual(self.student_1.department, self.dept_ece)

    def test_student_reset_password(self):
        reset_url = reverse('students:reset_password', kwargs={'pk': self.student_1.pk})
        
        # Load form
        response = self.client.get(reset_url)
        self.assertEqual(response.status_code, 200)
        
        # Reset password (too short)
        response = self.client.post(reset_url, {'password': '123'})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'password', "Password must be at least 6 characters long.")
        
        # Reset password (valid)
        response = self.client.post(reset_url, {'password': 'NewPassword123'})
        self.assertRedirects(response, self.list_url)
        
        # Verify password and flag updated
        self.student_user_1.refresh_from_db()
        self.assertTrue(self.student_user_1.check_password('NewPassword123'))
        self.assertTrue(self.student_user_1.must_change_password)

    def test_student_suspend_and_enable(self):
        suspend_url = reverse('students:suspend', kwargs={'pk': self.student_1.pk})
        
        # Active -> Suspended (is_active = False)
        response = self.client.post(suspend_url)
        self.assertRedirects(response, self.list_url)
        self.student_user_1.refresh_from_db()
        self.assertFalse(self.student_user_1.is_active)
        
        # Suspended -> Active (is_active = True)
        response = self.client.post(suspend_url)
        self.assertRedirects(response, self.list_url)
        self.student_user_1.refresh_from_db()
        self.assertTrue(self.student_user_1.is_active)

    def test_student_delete(self):
        delete_url = reverse('students:delete', kwargs={'pk': self.student_1.pk})
        
        # Load confirmation page
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Are you sure you want to delete student")

        # Post deletion
        response = self.client.post(delete_url)
        self.assertRedirects(response, self.list_url)
        
        # Verify both Student profile and User account deleted (on CASCADE)
        self.assertFalse(Student.objects.filter(pk=self.student_1.pk).exists())
        self.assertFalse(User.objects.filter(pk=self.student_user_1.pk).exists())

    def test_student_export_list(self):
        # Export with batch filter (should only export Alice Cooper)
        response = self.client.get(self.export_url, {'batch': self.batch_cse.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertTrue(response['Content-Disposition'].startswith('attachment; filename="students_list.csv"'))
        
        # Read CSV content
        content = response.content.decode('utf-8')
        self.assertIn("Alice Cooper", content)
        self.assertNotIn("Bob Miller", content)
