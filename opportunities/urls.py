from django.urls import path
from .views import (
    OpportunityListView,
    OpportunityVerifyView,
    OpportunityIgnoreView,
    OpportunityEditView,
    OpportunityImportCompanyView,
    OpportunityCreateDriveView,
    MockCareerPageView
)

app_name = 'opportunities'

urlpatterns = [
    path('', OpportunityListView.as_view(), name='list'),
    path('<int:pk>/verify/', OpportunityVerifyView.as_view(), name='verify'),
    path('<int:pk>/ignore/', OpportunityIgnoreView.as_view(), name='ignore'),
    path('<int:pk>/edit/', OpportunityEditView.as_view(), name='edit'),
    path('<int:pk>/import-company/', OpportunityImportCompanyView.as_view(), name='import_company'),
    path('<int:pk>/create-drive/', OpportunityCreateDriveView.as_view(), name='create_drive'),
    path('mock-career-page/', MockCareerPageView.as_view(), name='mock_career_page'),
]
