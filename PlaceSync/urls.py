"""
URL configuration for PlaceSync project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import HomeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('colleges/', include('colleges.urls')),
    path('departments/', include('departments.urls')),
    path('batches/', include('batches.urls')),
    path('students/', include('students.urls')),
    path('companies/', include('companies.urls')),
    path('placements/', include('placements.urls')),
    path('opportunities/', include('opportunities.urls')),
    path('communication/', include('communication.urls')),
    path('reports/', include('reports.urls')),
    path('analytics/', include('analytics.urls')),
    path('student/', include('student_portal.urls')),

    path('dashboard/access/', include('staff_permissions.urls')),
    path('', HomeView.as_view(), name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

