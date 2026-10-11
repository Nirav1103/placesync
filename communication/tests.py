from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core import mail
from django.core.management import call_command
from datetime import timedelta
import io

from colleges.models import College
from communication.models import EmailTemplate, SentEmail, Notification
from students.models import Student
from departments.models import Department
from batches.models import Batch

User = get_user_model()

class CommunicationTestCase(TestCase):
    def setUp(self):
        # Create college
        self.college = College.objects.create(
            name="Communication University",
            code="CU",
            website="https://cu.edu"
        )
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username="cu_admin",
            email="admin@cu.edu",
            password="adminpassword123",
            role=User.Role.COLLEGE_ADMIN,
            college=self.college
        )
        
        # Create department & batch
        self.department = Department.objects.create(college=self.college, name="Computer Engineering", code="CE")
        self.batch = Batch.objects.create(department=self.department, name="Batch CE 2026", graduation_year=2026)

        # Create student user & student profile
        self.student_user = User.objects.create_user(
            username="student_ce",
            email="student@cu.edu",
            password="studpassword123",
            role=User.Role.STUDENT,
            college=self.college
        )
        self.student = Student.objects.create(
            user=self.student_user,
            college=self.college,
            department=self.department,
            batch=self.batch,
            roll_number="CE001",
            name="Student CE",
            email="student@cu.edu"
        )

        self.client = Client()
        self.client.login(username="cu_admin", password="adminpassword123")

        self.dashboard_url = reverse('communication:dashboard')
        self.compose_url = reverse('communication:compose')

    def test_email_template_crud(self):
        # 1. Create Template
        create_url = reverse('communication:template_create')
        response = self.client.post(create_url, {
            'name': 'Test Tpl',
            'subject': 'Alert Test',
            'body': 'Dear {{ student_name }}, please update your profile.'
        })
        self.assertRedirects(response, self.dashboard_url)
        self.assertTrue(EmailTemplate.objects.filter(college=self.college, name='Test Tpl').exists())
        
        tpl = EmailTemplate.objects.get(college=self.college, name='Test Tpl')
        
        # 2. Edit Template
        edit_url = reverse('communication:template_edit', kwargs={'pk': tpl.pk})
        response = self.client.post(edit_url, {
            'name': 'Updated Tpl',
            'subject': 'Alert Updated',
            'body': 'Updated template body content.'
        })
        self.assertRedirects(response, self.dashboard_url)
        tpl.refresh_from_db()
        self.assertEqual(tpl.name, 'Updated Tpl')
        
        # 3. Delete Template
        delete_url = reverse('communication:template_delete', kwargs={'pk': tpl.pk})
        response = self.client.post(delete_url)
        self.assertRedirects(response, self.dashboard_url)
        self.assertFalse(EmailTemplate.objects.filter(pk=tpl.pk).exists())

    def test_compose_instant_broadcast_email(self):
        # Trigger immediate SMTP send to Students
        response = self.client.post(self.compose_url, {
            'recipient_type': SentEmail.RecipientType.STUDENTS,
            'target_batch': self.batch.pk,
            'target_department': self.department.pk,
            'subject': 'Immediate Broadcast Alert',
            'body': 'Instant email body.',
            'custom_recipients': ''
        })
        self.assertRedirects(response, self.dashboard_url)
        
        # Check database logs
        self.assertEqual(SentEmail.objects.filter(college=self.college).count(), 1)
        sent_email = SentEmail.objects.first()
        self.assertEqual(sent_email.status, SentEmail.SendStatus.SENT)
        self.assertIn('student@cu.edu', sent_email.recipients)

        # Check Django Outbox SMTP Mock
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Immediate Broadcast Alert')
        self.assertIn('student@cu.edu', mail.outbox[0].to)

        # Check in-app notification created for student
        self.assertTrue(Notification.objects.filter(user=self.student_user, title="New Announcement: Immediate Broadcast Alert").exists())

    def test_schedule_email_and_management_command(self):
        # Post scheduled email (scheduled for 1 hour in future)
        scheduled_time = timezone.now() + timedelta(hours=1)
        
        response = self.client.post(self.compose_url, {
            'recipient_type': SentEmail.RecipientType.CUSTOM,
            'custom_recipients': 'external@gmail.com',
            'subject': 'Scheduled Alert Message',
            'body': 'Scheduled email body.',
            'scheduled_time': scheduled_time.strftime('%Y-%m-%dT%H:%M')
        })
        self.assertRedirects(response, self.dashboard_url)
        
        # Check stored in PENDING status
        self.assertEqual(SentEmail.objects.filter(status=SentEmail.SendStatus.PENDING).count(), 1)
        pending_email = SentEmail.objects.get(status=SentEmail.SendStatus.PENDING)
        self.assertEqual(pending_email.subject, 'Scheduled Alert Message')
        
        # Run command right now -> should not send since scheduled_time is in future
        out = io.StringIO()
        call_command('send_scheduled_emails', stdout=out)
        self.assertIn("No pending scheduled emails found.", out.getvalue())
        self.assertEqual(SentEmail.objects.filter(status=SentEmail.SendStatus.PENDING).count(), 1)

        # Fast forward time: update scheduled_time to 1 hour in the past
        pending_email.scheduled_time = timezone.now() - timedelta(hours=1)
        pending_email.save()
        
        # Run command again -> should dispatch now
        out_sent = io.StringIO()
        call_command('send_scheduled_emails', stdout=out_sent)
        self.assertIn("Successfully sent scheduled email", out_sent.getvalue())
        
        pending_email.refresh_from_db()
        self.assertEqual(pending_email.status, SentEmail.SendStatus.SENT)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Scheduled Alert Message')

    def test_notification_read_action(self):
        # Create unread notification
        notification = Notification.objects.create(
            user=self.admin_user,
            title="Drive Notification",
            message="Amazon drive launched."
        )
        
        notifications_url = reverse('communication:notifications')
        response = self.client.get(notifications_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Amazon drive launched.")
        self.assertContains(response, "Mark Read")

        # Mark read POST
        read_url = reverse('communication:notification_read', kwargs={'pk': notification.pk})
        response = self.client.post(read_url)
        self.assertRedirects(response, notifications_url)
        
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
