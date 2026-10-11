from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.utils import timezone
from .models import PlacementDrive, Application
from communication.models import Notification
from students.models import Student

@receiver(post_save, sender=PlacementDrive)
def notify_eligible_students_on_drive_save(sender, instance, created, **kwargs):
    """
    Triggers when a PlacementDrive is created or updated.
    Sends notifications to all eligible students under the college.
    """
    # Delay sending if ManyToMany fields are not populated yet (e.g. eligible_departments).
    # We will trigger the main list building on save, but in Django, ManyToMany fields
    # are populated after saving. So we also bind to m2m_changed to notify properly!
    # Let's write a helper function to do the notification check.
    _send_drive_notifications(instance, created)

@receiver(m2m_changed, sender=PlacementDrive.eligible_departments.through)
def notify_eligible_students_m2m_dept(sender, instance, action, **kwargs):
    if action == "post_add":
        _send_drive_notifications(instance, created=True)

@receiver(m2m_changed, sender=PlacementDrive.eligible_batches.through)
def notify_eligible_students_m2m_batch(sender, instance, action, **kwargs):
    if action == "post_add":
        _send_drive_notifications(instance, created=True)


def _send_drive_notifications(instance, created):
    # Only notify for ACTIVE / UPCOMING drives
    if instance.status not in ['ACTIVE', 'UPCOMING']:
        # If cancelled
        if instance.status == 'COMPLETED':
            # Notify applied students that the drive is closed / cancelled
            applications = instance.applications.all()
            for app in applications:
                if app.student and app.student.user:
                    Notification.objects.get_or_create(
                        user=app.student.user,
                        title=f"Placement Drive Closed: {instance.role} at {instance.company.name}",
                        message=f"The placement drive for {instance.role} at {instance.company.name} has been closed or completed.",
                    )
        return

    # Find all students in this college
    students = Student.objects.filter(college=instance.college)

    # Pre-fetch eligible M2M sets if populated
    eligible_depts = list(instance.eligible_departments.all())
    eligible_batches = list(instance.eligible_batches.all())

    for student in students:
        eligible = True

        # Check Department (if departments are specified)
        if eligible_depts and student.department not in eligible_depts:
            eligible = False

        # Check Batch (if batches are specified)
        if eligible_batches and student.batch not in eligible_batches:
            eligible = False

        # Check CGPA
        if student.cgpa is not None and student.cgpa < instance.min_cgpa:
            eligible = False

        # Check Backlogs
        if student.backlogs > instance.max_backlogs:
            eligible = False

        if eligible:
            title = f"New Drive: {instance.role} at {instance.company.name}" if created else f"Drive Updated: {instance.role} at {instance.company.name}"
            msg = (
                f"A new placement drive for the role of '{instance.role}' at {instance.company.name} is now open! "
                f"Deadline: {instance.deadline or 'N/A'}. Minimum CGPA: {instance.min_cgpa}."
            ) if created else (
                f"The details of the placement drive for '{instance.role}' at {instance.company.name} have been updated. Please review."
            )

            # Avoid duplicates on repeated edits
            if student.user:
                Notification.objects.get_or_create(
                    user=student.user,
                    title=title,
                    message=msg
                )


@receiver(post_save, sender=Application)
def notify_student_on_application_status_change(sender, instance, created, **kwargs):
    """
    Triggers when a student's Application status changes.
    Dispatches: Interview Reminder / Offer Released.
    """
    if not (instance.student and instance.student.user):
        return

    if created:
        # Successfully Applied Notification
        Notification.objects.get_or_create(
            user=instance.student.user,
            title=f"Applied: {instance.drive.role} at {instance.drive.company.name}",
            message=f"Your application for {instance.drive.role} at {instance.drive.company.name} has been submitted successfully."
        )
        return

    # Status changes
    if instance.status == 'SHORTLISTED':
        # Interview Reminder
        Notification.objects.get_or_create(
            user=instance.student.user,
            title=f"Interview Invitation: {instance.drive.role} at {instance.drive.company.name}",
            message=f"Congratulations! You have been shortlisted for the interview round of {instance.drive.role} at {instance.drive.company.name}."
        )
    elif instance.status == 'SELECTED':
        # Offer Released
        Notification.objects.get_or_create(
            user=instance.student.user,
            title=f"Job Offer Released: {instance.drive.role} at {instance.drive.company.name} 🎉",
            message=f"Wonderful news! You have been selected for the role of {instance.drive.role} at {instance.drive.company.name}."
        )
    elif instance.status == 'REJECTED':
        Notification.objects.get_or_create(
            user=instance.student.user,
            title=f"Application Update: {instance.drive.role} at {instance.drive.company.name}",
            message=f"Thank you for participating. Your application status for {instance.drive.role} at {instance.drive.company.name} has been updated."
        )
