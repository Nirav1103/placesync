from django.urls import path
from .views import (
    DepartmentListView,
    DepartmentCreateView,
    DepartmentUpdateView,
    DepartmentDeleteView
)

app_name = 'departments'

urlpatterns = [
    path('', DepartmentListView.as_view(), name='list'),
    path('add/', DepartmentCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', DepartmentUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', DepartmentDeleteView.as_view(), name='delete'),
]
