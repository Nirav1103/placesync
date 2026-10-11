from django.urls import path
from .views import (
    EmailCenterDashboardView,
    TemplateCreateView,
    TemplateUpdateView,
    TemplateDeleteView,
    ComposeEmailView,
    NotificationListView,
    MarkNotificationReadView
)

app_name = 'communication'

urlpatterns = [
    path('', EmailCenterDashboardView.as_view(), name='dashboard'),
    path('templates/add/', TemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/edit/', TemplateUpdateView.as_view(), name='template_edit'),
    path('templates/<int:pk>/delete/', TemplateDeleteView.as_view(), name='template_delete'),
    path('compose/', ComposeEmailView.as_view(), name='compose'),
    path('notifications/', NotificationListView.as_view(), name='notifications'),
    path('notifications/<int:pk>/read/', MarkNotificationReadView.as_view(), name='notification_read'),
]
