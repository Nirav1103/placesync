from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator

from accounts.models import User
from .models import StaffMember
from .utils import is_college_admin

class CollegeAdminRequiredMixin(AccessMixin):
    """Mixin to ensure only the primary College Admin can access administrative pages."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not is_college_admin(request.user):
            return render(request, 'staff_permissions/403.html', status=403)
        return super().dispatch(request, *args, **kwargs)


class SettingsView(CollegeAdminRequiredMixin, View):
    """Landing settings page showing administration options."""
    template_name = 'staff_permissions/settings.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


class StaffListView(CollegeAdminRequiredMixin, View):
    """List staff members with status cards, search, and filters."""
    template_name = 'staff_permissions/staff_list.html'

    def get(self, request, *args, **kwargs):
        college = request.user.college
        
        # Calculate status counts
        total_staff = StaffMember.objects.filter(college=college).count()
        active_staff = StaffMember.objects.filter(college=college, user__is_active=True).count()
        inactive_staff = StaffMember.objects.filter(college=college, user__is_active=False).count()

        # Query staff list
        staff_list = StaffMember.objects.filter(college=college).select_related('user')

        # Apply search
        q = request.GET.get('q', '').strip()
        if q:
            staff_list = staff_list.filter(
                Q(user__first_name__icontains=q) |
                Q(user__last_name__icontains=q) |
                Q(user__username__icontains=q) |
                Q(user__email__icontains=q)
            )

        # Apply role filter
        role_filter = request.GET.get('role', '')
        if role_filter:
            staff_list = staff_list.filter(role=role_filter)

        # Apply status filter
        status_filter = request.GET.get('status', '')
        if status_filter == 'active':
            staff_list = staff_list.filter(user__is_active=True)
        elif status_filter == 'inactive':
            staff_list = staff_list.filter(user__is_active=False)

        # Pagination
        paginator = Paginator(staff_list, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, self.template_name, {
            'page_obj': page_obj,
            'total_staff': total_staff,
            'active_staff': active_staff,
            'inactive_staff': inactive_staff,
            'q': q,
            'selected_role': role_filter,
            'selected_status': status_filter,
        })


class StaffCreateView(CollegeAdminRequiredMixin, View):
    """Directly add a new staff member account."""
    template_name = 'staff_permissions/staff_form.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'action': 'Create',
            'roles': StaffMember.RoleChoices.choices,
        })

    def post(self, request, *args, **kwargs):
        college = request.user.college
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        role = request.POST.get('role', '')
        is_active = request.POST.get('status') == 'active'

        # Validation
        errors = False
        if not full_name:
            messages.error(request, "Full name is required.")
            errors = True
        if not email:
            messages.error(request, "Email is required.")
            errors = True
        if not username:
            messages.error(request, "Username is required.")
            errors = True
        elif User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' is already taken.")
            errors = True

        if not password:
            messages.error(request, "Password is required.")
            errors = True
        elif password != confirm_password:
            messages.error(request, "Passwords do not match.")
            errors = True

        if role not in [StaffMember.RoleChoices.EDITOR, StaffMember.RoleChoices.VIEW_ONLY]:
            messages.error(request, "Invalid role selected.")
            errors = True

        if errors:
            return render(request, self.template_name, {
                'action': 'Create',
                'roles': StaffMember.RoleChoices.choices,
                'full_name': full_name,
                'email': email,
                'username': username,
                'role': role,
                'status': 'active' if is_active else 'inactive',
            })

        # Name Split
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        # Create account immediately
        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password,
                role=User.Role.COLLEGE_ADMIN,
                college=college,
                is_active=is_active
            )

            profile_pic = request.FILES.get('profile_picture')

            StaffMember.objects.create(
                user=user,
                college=college,
                role=role,
                profile_picture=profile_pic
            )

        messages.success(request, f"Staff member '{username}' account created successfully.")
        return redirect('staff_permissions:staff_list')


class StaffUpdateView(CollegeAdminRequiredMixin, View):
    """Edit basic staff member details."""
    template_name = 'staff_permissions/staff_form.html'

    def get(self, request, pk, *args, **kwargs):
        college = request.user.college
        staff = get_object_or_404(StaffMember, pk=pk, college=college)
        return render(request, self.template_name, {
            'action': 'Edit',
            'staff': staff,
            'roles': StaffMember.RoleChoices.choices,
        })

    def post(self, request, pk, *args, **kwargs):
        college = request.user.college
        staff = get_object_or_404(StaffMember, pk=pk, college=college)
        user = staff.user

        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', '')
        is_active = request.POST.get('status') == 'active'

        # Validation
        errors = False
        if not full_name:
            messages.error(request, "Full name is required.")
            errors = True
        if not email:
            messages.error(request, "Email is required.")
            errors = True
        if role not in [StaffMember.RoleChoices.EDITOR, StaffMember.RoleChoices.VIEW_ONLY]:
            messages.error(request, "Invalid role selected.")
            errors = True

        if errors:
            return render(request, self.template_name, {
                'action': 'Edit',
                'staff': staff,
                'roles': StaffMember.RoleChoices.choices,
            })

        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        with transaction.atomic():
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = is_active
            user.save()

            profile_pic = request.FILES.get('profile_picture')
            if profile_pic:
                staff.profile_picture = profile_pic

            staff.role = role
            staff.save()

        messages.success(request, f"Staff member '{user.username}' updated successfully.")
        return redirect('staff_permissions:staff_list')


class StaffDeleteView(CollegeAdminRequiredMixin, View):
    """Delete a staff member user account and profile."""
    def post(self, request, pk, *args, **kwargs):
        college = request.user.college
        staff = get_object_or_404(StaffMember, pk=pk, college=college)
        user = staff.user
        username = user.username
        user.delete()
        messages.success(request, f"Staff member '{username}' deleted successfully.")
        return redirect('staff_permissions:staff_list')


class StaffResetPasswordView(CollegeAdminRequiredMixin, View):
    """Directly reset password for any staff account by College Admin."""
    template_name = 'staff_permissions/staff_reset_password.html'

    def get(self, request, pk, *args, **kwargs):
        college = request.user.college
        staff = get_object_or_404(StaffMember, pk=pk, college=college)
        return render(request, self.template_name, {
            'staff': staff,
        })

    def post(self, request, pk, *args, **kwargs):
        college = request.user.college
        staff = get_object_or_404(StaffMember, pk=pk, college=college)
        user = staff.user

        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if not password:
            messages.error(request, "Password is required.")
            return render(request, self.template_name, {
                'staff': staff,
            })

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, self.template_name, {
                'staff': staff,
            })

        user.set_password(password)
        user.save()

        messages.success(request, f"Password reset successfully for '{user.username}'.")
        return redirect('staff_permissions:staff_list')


class StaffDetailView(CollegeAdminRequiredMixin, View):
    """View details of a staff member."""
    template_name = 'staff_permissions/staff_detail.html'

    def get(self, request, pk, *args, **kwargs):
        college = request.user.college
        staff = get_object_or_404(StaffMember, pk=pk, college=college)
        return render(request, self.template_name, {
            'staff': staff,
        })


class ChangePasswordView(LoginRequiredMixin, View):
    template_name = 'staff_permissions/change_password.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        current_pw = request.POST.get('current_password', '').strip()
        new_pw = request.POST.get('new_password', '').strip()
        confirm_pw = request.POST.get('confirm_password', '').strip()

        errors = False
        if not current_pw or not new_pw or not confirm_pw:
            messages.error(request, "All fields are required.")
            errors = True
        
        # Authenticate current password check
        if not request.user.check_password(current_pw):
            messages.error(request, "Incorrect current password.")
            errors = True

        if new_pw != confirm_pw:
            messages.error(request, "New password and password confirmation do not match.")
            errors = True

        if errors:
            return render(request, self.template_name)

        request.user.set_password(new_pw)
        request.user.save()
        update_session_auth_hash(request, request.user)

        messages.success(request, "Password changed successfully!")
        
        # Redirect back to settings page if college admin, otherwise to index
        if is_college_admin(request.user):
            return redirect('staff_permissions:settings')
        return redirect('dashboard:index')
