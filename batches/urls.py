from django.urls import path
from .views import (
    BatchListView,
    BatchCreateView,
    BatchUpdateView,
    BatchDeleteView,
    BatchDashboardView,
    BatchStudentImportView,
    BatchStudentImportPreviewView,
    BatchStudentImportReportView
)

app_name = 'batches'

urlpatterns = [
    path('', BatchListView.as_view(), name='list'),
    path('add/', BatchCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', BatchUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', BatchDeleteView.as_view(), name='delete'),
    path('<int:pk>/dashboard/', BatchDashboardView.as_view(), name='dashboard'),
    path('<int:pk>/import/', BatchStudentImportView.as_view(), name='import_students'),
    path('<int:pk>/import/preview/', BatchStudentImportPreviewView.as_view(), name='import_preview'),
    path('<int:pk>/import/report/', BatchStudentImportReportView.as_view(), name='import_report'),
]
