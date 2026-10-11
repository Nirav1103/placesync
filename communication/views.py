from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import Http404, HttpResponseForbidden
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
from django.db import transaction

from .models import EmailTemplate, SentEmail, Notification
from .forms import EmailTemplateForm, ComposeEmailForm
from students.models import Student
from companies.models import Company
from accounts.models import User

class EmailCenterDashboardView(LoginRequiredMixin, View):
    template_name = 'communication/dashboard.html'

    def get(self, request, *args, **kwargs):
        college = request.user.college
        if not college:
            raise Http404("No college associated with your account.")

        if request.user.role != 'COLLEGE_ADMIN':
            return redirect('communication:notifications')

        templates = EmailTemplate.objects.filter(college=college)
        sent_emails = SentEmail.objects.filter(college=college).select_related('sender')

        context = {
            'templates': templates,
            'sent_emails': sent_emails
        }
        return render(request, self.template_name, context)

class TemplateCreateView(LoginRequiredMixin, View):
    template_name = 'communication/template_form.html'
    form_class = EmailTemplateForm

    def get(self, request, *args, **kwargs):
        if request.user.role != 'COLLEGE_ADMIN':
            return HttpResponseForbidden()
        form = self.form_class()
        return render(request, self.template_name, {'form': form, 'action': 'Create'})

    def post(self, request, *args, **kwargs):
        if request.user.role != 'COLLEGE_ADMIN':
            return HttpResponseForbidden()
        form = self.form_class(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.college = request.user.college
            
            # Check unique template name per college case-insensitively
            if EmailTemplate.objects.filter(college=request.user.college, name__iexact=template.name).exists():
                form.add_error('name', "A template with this name already exists in your college.")
                return render(request, self.template_name, {'form': form, 'action': 'Create'})
                
            template.save()
            messages.success(request, f"Email Template '{template.name}' created successfully.")
            return redirect('communication:dashboard')
        return render(request, self.template_name, {'form': form, 'action': 'Create'})

class TemplateUpdateView(LoginRequiredMixin, View):
    template_name = 'communication/template_form.html'
    form_class = EmailTemplateForm

    def get(self, request, pk, *args, **kwargs):
        if request.user.role != 'COLLEGE_ADMIN':
            return HttpResponseForbidden()
        template = get_object_or_404(EmailTemplate, pk=pk, college=request.user.college)
        form = self.form_class(instance=template)
        return render(request, self.template_name, {'form': form, 'action': 'Update'})

    def post(self, request, pk, *args, **kwargs):
        if request.user.role != 'COLLEGE_ADMIN':
            return HttpResponseForbidden()
        template = get_object_or_404(EmailTemplate, pk=pk, college=request.user.college)
        form = self.form_class(request.POST, instance=template)
        if form.is_valid():
            # Check uniqueness
            qs = EmailTemplate.objects.filter(college=request.user.college, name__iexact=form.cleaned_data['name']).exclude(pk=pk)
            if qs.exists():
                form.add_error('name', "A template with this name already exists in your college.")
                return render(request, self.template_name, {'form': form, 'action': 'Update'})
                
            form.save()
            messages.success(request, f"Template details updated.")
            return redirect('communication:dashboard')
        return render(request, self.template_name, {'form': form, 'action': 'Update'})

class TemplateDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        if request.user.role != 'COLLEGE_ADMIN':
            return HttpResponseForbidden()
        template = get_object_or_404(EmailTemplate, pk=pk, college=request.user.college)
        name = template.name
        template.delete()
        messages.success(request, f"Template '{name}' has been deleted successfully.")
        return redirect('communication:dashboard')

class ComposeEmailView(LoginRequiredMixin, View):
    template_name = 'communication/compose.html'
    form_class = ComposeEmailForm

    def get(self, request, *args, **kwargs):
        if request.user.role != 'COLLEGE_ADMIN':
            return HttpResponseForbidden()

        # Handle prefill using template parameter
        template_id = request.GET.get('template_id')
        initial_data = {}
        if template_id:
            tpl = EmailTemplate.objects.filter(pk=template_id, college=request.user.college).first()
            if tpl:
                initial_data = {
                    'template': tpl.pk,
                    'subject': tpl.subject,
                    'body': tpl.body
                }

        form = self.form_class(college=request.user.college, initial=initial_data)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        if request.user.role != 'COLLEGE_ADMIN':
            return HttpResponseForbidden()

        form = self.form_class(request.POST, request.FILES, college=request.user.college)
        if form.is_valid():
            recipient_type = form.cleaned_data['recipient_type']
            target_batch = form.cleaned_data['target_batch']
            target_department = form.cleaned_data['target_department']
            custom_recipients_str = form.cleaned_data['custom_recipients']
            subject = form.cleaned_data['subject']
            body = form.cleaned_data['body']
            scheduled_time = form.cleaned_data['scheduled_time']
            attachment = request.FILES.get('attachment')

            # Calculate recipient list
            recipient_emails = []
            users_to_notify = [] # system users to send in-app notification

            if recipient_type == SentEmail.RecipientType.STUDENTS:
                students_qs = Student.objects.filter(college=request.user.college)
                if target_batch:
                    students_qs = students_qs.filter(batch=target_batch)
                if target_department:
                    students_qs = students_qs.filter(department=target_department)
                
                for s in students_qs:
                    recipient_emails.append(s.email)
                    if s.user:
                        users_to_notify.append(s.user)
            elif recipient_type == SentEmail.RecipientType.COMPANIES:
                companies_qs = Company.objects.filter(college=request.user.college)
                for c in companies_qs:
                    if c.hr_email:
                        recipient_emails.append(c.hr_email)
            else:
                # Custom
                emails = [email.strip() for email in custom_recipients_str.split(',') if email.strip()]
                recipient_emails.extend(emails)

            if not recipient_emails:
                messages.error(request, "Recipient query matches 0 email targets. Message was not queued.")
                return render(request, self.template_name, {'form': form})

            # Check if scheduled for future
            is_scheduled = False
            if scheduled_time and scheduled_time > timezone.now():
                is_scheduled = True

            with transaction.atomic():
                sent_email = SentEmail.objects.create(
                    college=request.user.college,
                    sender=request.user,
                    recipient_type=recipient_type,
                    recipients=", ".join(recipient_emails),
                    subject=subject,
                    body=body,
                    attachment=attachment,
                    scheduled_time=scheduled_time if is_scheduled else None,
                    status=SentEmail.SendStatus.PENDING if is_scheduled else SentEmail.SendStatus.SENT
                )

                if is_scheduled:
                    # Log audit notification
                    Notification.objects.create(
                        user=request.user,
                        title="Bulk Email Scheduled",
                        message=f"Your message '{subject}' has been scheduled to send on {scheduled_time.strftime('%Y-%m-%d %H:%M')}."
                    )
                    messages.success(request, f"Email scheduled successfully to dispatch on {scheduled_time.strftime('%Y-%m-%d %H:%M')}.")
                else:
                    # Send immediate email
                    email_msg = EmailMessage(
                        subject=subject,
                        body=body,
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@placesync.edu'),
                        to=recipient_emails
                    )
                    if attachment:
                        email_msg.attach(attachment.name, attachment.read(), attachment.content_type)
                    
                    try:
                        email_msg.send()
                        sent_email.sent_at = timezone.now()
                        sent_email.save()
                        
                        # Generate in-app notifications for targeted system users
                        for user in users_to_notify:
                            Notification.objects.create(
                                user=user,
                                title=f"New Announcement: {subject}",
                                message=body
                            )
                        messages.success(request, f"Announcements dispatched successfully via SMTP to {len(recipient_emails)} targets.")
                    except Exception as e:
                        sent_email.status = SentEmail.SendStatus.FAILED
                        sent_email.save()
                        messages.error(request, f"SMTP dispatch failed: {e}")

            return redirect('communication:dashboard')

        return render(request, self.template_name, {'form': form})

class NotificationListView(LoginRequiredMixin, View):
    template_name = 'communication/notification_list.html'

    def get(self, request, *args, **kwargs):
        notifications = Notification.objects.filter(user=request.user)
        return render(request, self.template_name, {'notifications': notifications})

class MarkNotificationReadView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save()
        return redirect('communication:notifications')
