from django.urls import path
from .views import (
    SettingsView, StaffListView, StaffCreateView,
    StaffUpdateView, StaffDeleteView, StaffResetPasswordView,
    ChangePasswordView, StaffDetailView
)

app_name = 'staff_permissions'

urlpatterns = [
    path('settings/', SettingsView.as_view(), name='settings'),
    path('settings/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('staff/', StaffListView.as_view(), name='staff_list'),
    path('staff/add/', StaffCreateView.as_view(), name='staff_create'),
    path('staff/<int:pk>/', StaffDetailView.as_view(), name='staff_detail'),
    path('staff/<int:pk>/edit/', StaffUpdateView.as_view(), name='staff_update'),
    path('staff/<int:pk>/delete/', StaffDeleteView.as_view(), name='staff_delete'),
    path('staff/<int:pk>/reset-password/', StaffResetPasswordView.as_view(), name='staff_reset_password'),
]
