from django.urls import path
from .views import CollegeProfileDetailView, CollegeProfileEditView

app_name = 'colleges'

urlpatterns = [
    path('profile/', CollegeProfileDetailView.as_view(), name='profile_detail'),
    path('profile/edit/', CollegeProfileEditView.as_view(), name='profile_edit'),
]
