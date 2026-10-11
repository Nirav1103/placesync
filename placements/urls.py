from django.urls import path
from .views import (
    PlacementDriveListView,
    PlacementDriveCreateView,
    PlacementDriveDetailView,
    StudentApplyView,
    UpdateApplicationStatusView
)

app_name = 'placements'

urlpatterns = [
    path('', PlacementDriveListView.as_view(), name='list'),
    path('add/', PlacementDriveCreateView.as_view(), name='create'),
    path('<int:pk>/', PlacementDriveDetailView.as_view(), name='detail'),
    path('<int:pk>/apply/', StudentApplyView.as_view(), name='apply'),
    path('applications/<int:app_pk>/status/<str:new_status>/', UpdateApplicationStatusView.as_view(), name='update_status'),
]
