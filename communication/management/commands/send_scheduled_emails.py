from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
from django.db import transaction

from communication.models import SentEmail, Notification
from students.models import Student

class Command(BaseCommand):
    help = 'Dispatches scheduled emails whose scheduled time is in the past.'

    def handle(self, *args, **options):
        now = timezone.now()
        pending_emails = SentEmail.objects.filter(
            status=SentEmail.SendStatus.PENDING,
            scheduled_time__lte=now
        )

        if not pending_emails.exists():
            self.stdout.write("No pending scheduled emails found.")
            return

        self.stdout.write(f"Found {pending_emails.count()} pending scheduled email(s). Processing...")

        for email_record in pending_emails:
            recipient_list = [email.strip() for email in email_record.recipients.split(',') if email.strip()]
            
            email_msg = EmailMessage(
                subject=email_record.subject,
                body=email_record.body,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@placesync.edu'),
                to=recipient_list
            )
            
            if email_record.attachment:
                # Open file in binary mode
                try:
                    email_record.attachment.open('rb')
                    email_msg.attach(
                        email_record.attachment.name,
                        email_record.attachment.read()
                    )
                except Exception as file_err:
                    self.stderr.write(f"Failed to read attachment for email record {email_record.id}: {file_err}")
                finally:
                    email_record.attachment.close()

            try:
                with transaction.atomic():
                    email_msg.send()
                    email_record.status = SentEmail.SendStatus.SENT
                    email_record.sent_at = timezone.now()
                    email_record.save()
                    
                    # Generate in-app notifications if recipient matches system users (by email address)
                    students_qs = Student.objects.filter(college=email_record.college, email__in=recipient_list)
                    for student in students_qs:
                        if student.user:
                            Notification.objects.create(
                                user=student.user,
                                title=f"Announcements: {email_record.subject}",
                                message=email_record.body
                            )
                            
                    self.stdout.write(self.style.SUCCESS(f"Successfully sent scheduled email '{email_record.subject}' to {len(recipient_list)} targets."))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed to send scheduled email '{email_record.subject}': {e}"))
                email_record.status = SentEmail.SendStatus.FAILED
                email_record.save()
