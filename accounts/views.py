from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib import messages
from django.urls import reverse_lazy
from .forms import CollegeRegistrationForm, CollegeLoginForm


# ─── Admin: Registration ──────────────────────────────────────────────────────
class CollegeRegistrationView(View):
    form_class = CollegeRegistrationForm
    template_name = 'accounts/register.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to PlaceSync, {user.college.name} Admin!")
            return redirect('dashboard:index')
        return render(request, self.template_name, {'form': form})


# ─── Admin: Login ─────────────────────────────────────────────────────────────
class CollegeLoginView(LoginView):
    authentication_form = CollegeLoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = False

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # If logged in as a STUDENT and trying to access College Admin login,
            # log out student session so user can enter College Admin credentials.
            if getattr(request.user, 'role', None) == 'STUDENT':
                logout(request)
                messages.info(request, "Student session ended. Please log in with your College Admin credentials.")
                return super().dispatch(request, *args, **kwargs)
            else:
                return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        # Ensure student accounts do not log in via College Admin form
        if hasattr(user, 'role') and user.role == 'STUDENT':
            messages.error(
                self.request,
                "Student accounts cannot log in through the College Admin Portal. Please use Student Login."
            )
            return self.form_invalid(form)
        return super().form_valid(form)


# ─── Student: Login ───────────────────────────────────────────────────────────
class StudentLoginView(LoginView):
    template_name = 'accounts/student_login.html'
    redirect_authenticated_user = False

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # If logged in as an ADMIN/STAFF and trying to access Student login,
            # log out admin session so user can enter Student credentials.
            if getattr(request.user, 'role', None) != 'STUDENT':
                logout(request)
                messages.info(request, "Admin session ended. Please log in with your Student credentials.")
                return super().dispatch(request, *args, **kwargs)
            else:
                return redirect('student_portal:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        user = self.request.user
        if hasattr(user, 'role') and user.role == 'STUDENT':
            return reverse_lazy('student_portal:dashboard')
        return reverse_lazy('dashboard:index')

    def form_valid(self, form):
        user = form.get_user()
        # Ensure only students use this login page
        if hasattr(user, 'role') and user.role != 'STUDENT':
            messages.error(
                self.request,
                "This login page is for students only. "
                "Please use the admin login page."
            )
            return self.form_invalid(form)
        return super().form_valid(form)



# ─── Shared: Logout ───────────────────────────────────────────────────────────
class CollegeLogoutView(View):
    def get(self, request, *args, **kwargs):
        role = getattr(request.user, 'role', None) if request.user.is_authenticated else None
        logout(request)
        messages.info(request, "You have been logged out successfully.")
        if role == 'STUDENT':
            return redirect('accounts:student_login')
        return redirect('accounts:login')

    def post(self, request, *args, **kwargs):
        role = getattr(request.user, 'role', None) if request.user.is_authenticated else None
        logout(request)
        messages.info(request, "You have been logged out successfully.")
        if role == 'STUDENT':
            return redirect('accounts:student_login')
        return redirect('accounts:login')


# ─── Force Password Change (shared for both admin & student) ──────────────────
class StudentPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/student_password_change.html'

    def get_success_url(self):
        user = self.request.user
        if hasattr(user, 'role') and user.role == 'STUDENT':
            return reverse_lazy('student_portal:dashboard')
        return reverse_lazy('dashboard:index')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        user.must_change_password = False
        user.save()
        messages.success(
            self.request,
            "Password changed successfully! Welcome to PlaceSync."
        )
        return response


# ─── Public Landing Page View ───────────────────────────────────────────────────
from django.views.generic import TemplateView

class HomeView(TemplateView):
    template_name = 'home.html'




