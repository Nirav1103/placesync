from django.urls import path
from .views import (
    StudentListView,
    StudentEditView,
    StudentDeleteView,
    StudentSuspendView,
    StudentResetPasswordView,
    StudentMoveView,
    StudentExportView
)

app_name = 'students'

urlpatterns = [
    path('', StudentListView.as_view(), name='list'),
    path('<int:pk>/edit/', StudentEditView.as_view(), name='edit'),
    path('<int:pk>/delete/', StudentDeleteView.as_view(), name='delete'),
    path('<int:pk>/suspend/', StudentSuspendView.as_view(), name='suspend'),
    path('<int:pk>/reset-password/', StudentResetPasswordView.as_view(), name='reset_password'),
    path('<int:pk>/move/', StudentMoveView.as_view(), name='move'),
    path('export/', StudentExportView.as_view(), name='export'),
]
