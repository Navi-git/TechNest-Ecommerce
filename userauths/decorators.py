from django.http import HttpResponseForbidden
from functools import wraps

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Authentication required.")

            # Allow superusers to access all views
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Ensure user has a valid role
            if not hasattr(request.user, 'role') or request.user.role not in allowed_roles:
                return HttpResponseForbidden("Access Denied.")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
