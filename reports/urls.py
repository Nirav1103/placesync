from django.urls import path
from .views import ReportsDashboardView, ViewReportView, ExportReportView

app_name = 'reports'

urlpatterns = [
    path('', ReportsDashboardView.as_view(), name='dashboard'),
    path('<str:report_type>/', ViewReportView.as_view(), name='view_report'),
    path('<str:report_type>/export/<str:export_format>/', ExportReportView.as_view(), name='export_report'),
]
