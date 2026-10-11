from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if getattr(request.user, 'must_change_password', False):
                change_url = reverse('accounts:password_change')
                logout_url = reverse('accounts:logout')
                student_login_url = reverse('accounts:student_login')

                allowed = [change_url, logout_url, student_login_url]

                skip = (
                    request.path in allowed
                    or request.path.startswith('/static/')
                    or request.path.startswith('/media/')
                )
                if not skip:
                    return redirect('accounts:password_change')

        return self.get_response(request)

