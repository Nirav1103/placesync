from django.urls import path
from .views import DashboardIndexView

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardIndexView.as_view(), name='index'),
]
