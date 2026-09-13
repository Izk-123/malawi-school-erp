"""Role-based access control mixins & decorators used across every app."""
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from functools import wraps


def _log_denied(request, roles):
    try:
        from .models import AuditLog
        user = request.user if request.user.is_authenticated else None
        AuditLog.objects.create(
            user=user,
            action=AuditLog.Action.PERMISSION_DENIED,
            username_attempted=getattr(user, 'username', ''),
            ip_address=request.META.get('REMOTE_ADDR'),
            detail=f'Tried to access a view requiring roles={roles} at {request.path}',
        )
    except Exception:
        # Never let audit logging break the actual permission check.
        pass


class RoleRequiredMixin(UserPassesTestMixin):
    """Class-based-view mixin: set `allowed_roles = ['admin', 'teacher']`."""
    allowed_roles = []
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (
            user.is_superuser or user.role in self.allowed_roles
        )

    def handle_no_permission(self):
        # AC-19: unauthorised access attempts shall be logged.
        _log_denied(self.request, self.allowed_roles)
        return super().handle_no_permission()


def role_required(*roles):
    """Function-based-view decorator equivalent of RoleRequiredMixin."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied
            if request.user.is_superuser or request.user.role in roles:
                return view_func(request, *args, **kwargs)
            _log_denied(request, roles)
            raise PermissionDenied
        return _wrapped
    return decorator

