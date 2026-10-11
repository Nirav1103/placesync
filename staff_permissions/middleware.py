from django.shortcuts import render
from django.urls import reverse

class SimpleAccessControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Check if user is a staff member (has staff_profile)
            if hasattr(request.user, 'staff_profile'):
                profile = request.user.staff_profile
                role = profile.role
                path = request.path
                method = request.method

                # Resolve safe paths
                change_password_url = reverse('staff_permissions:change_password')
                logout_url = reverse('accounts:logout')

                # 1. Staff users (Editor & View Only) cannot access settings or staff management
                if path.startswith('/dashboard/access/') and path != change_password_url:
                    return render(request, 'staff_permissions/403.html', status=403)

                # 2. View Only restrictions — block ALL write operations
                if role == 'VIEW_ONLY':
                    # Allow safe paths unconditionally
                    safe_paths = [change_password_url, logout_url]
                    if path in safe_paths:
                        return self.get_response(request)

                    # Block all non-GET/HEAD methods (POST, PUT, PATCH, DELETE)
                    if method not in ('GET', 'HEAD', 'OPTIONS'):
                        return render(request, 'staff_permissions/403.html', status=403)

                    # Block GET requests to write-intent URLs
                    write_keywords = [
                        '/create/', '/add/', '/edit/', '/update/', '/delete/',
                        '/verify/', '/approve/', '/suspend/', '/reset-password/',
                        '/move/', '/export/', '/apply/', '/ignore/',
                        '/import-company/', '/create-drive/', '/compose/',
                        '/verify-audit/',
                    ]
                    if any(keyword in path for keyword in write_keywords):
                        return render(request, 'staff_permissions/403.html', status=403)

        return self.get_response(request)
