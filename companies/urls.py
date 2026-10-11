from django.urls import path
from .views import (
    CompanyListView,
    CompanyCreateView,
    CompanyDetailView,
    CompanyUpdateView,
    CompanyDeleteView,
    CompanyVerificationDashboardView,
    CompanyVerificationAuditView
)

app_name = 'companies'

urlpatterns = [
    path('', CompanyListView.as_view(), name='list'),
    path('add/', CompanyCreateView.as_view(), name='create'),
    path('verification/', CompanyVerificationDashboardView.as_view(), name='verification_dashboard'),
    path('<int:pk>/', CompanyDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', CompanyUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', CompanyDeleteView.as_view(), name='delete'),
    path('<int:pk>/verify-audit/', CompanyVerificationAuditView.as_view(), name='verify_audit'),
]
