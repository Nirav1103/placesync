from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import (
    CollegeRegistrationView, CollegeLoginView, CollegeLogoutView,
    StudentLoginView, StudentPasswordChangeView,
)

app_name = 'accounts'

urlpatterns = [
    # Admin auth
    path('register/', CollegeRegistrationView.as_view(), name='register'),
    path('login/', CollegeLoginView.as_view(), name='login'),
    path('logout/', CollegeLogoutView.as_view(), name='logout'),

    # Student auth
    path('student/login/', StudentLoginView.as_view(), name='student_login'),

    # Force password change (works for both admin and student)
    path('password_change/', StudentPasswordChangeView.as_view(), name='password_change'),

    # Password Reset flow
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url=reverse_lazy('accounts:password_reset_done')
    ), name='password_reset'),

    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url=reverse_lazy('accounts:password_reset_complete')
    ), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
]
