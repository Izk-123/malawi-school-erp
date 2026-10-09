"""Role-based access control mixins & decorators used across every app.

Two layers:
  - RoleRequiredMixin / role_required: coarse portal gate (which dashboard
    a role may reach).
  - CanCreateAccountMixin / can_create_account_required: the governance
    doc's account-creation gate, delegated to
    `accounts.services.can_create_account_for` so the matrix lives in one
    place.
"""
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


# ---------------------------------------------------------------------------
# Governance: account-creation gate (doc §2)
# ---------------------------------------------------------------------------
class CanCreateAccountMixin(UserPassesTestMixin):
    """Class-based-view gate for anything that issues an invitation or
    creates a user account directly.

    Subclasses must set `account_creation_purpose` to one of the
    InvitationToken.Purpose values. The permission check is delegated to
    `accounts.services.can_create_account_for`, so the rule lives in one
    place (doc §2)."""
    account_creation_purpose = None
    raise_exception = True

    def test_func(self):
        from .services import can_create_account_for
        purpose = self.account_creation_purpose
        if not purpose:
            return False
        return can_create_account_for(self.request.user, purpose)

    def handle_no_permission(self):
        _log_denied(
            self.request,
            [self.account_creation_purpose or 'account_creation'],
        )
        return super().handle_no_permission()


def can_create_account_required(purpose):
    """Function-based-view equivalent of CanCreateAccountMixin."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            from .services import can_create_account_for
            if not can_create_account_for(request.user, purpose):
                _log_denied(request, [purpose])
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator

# ---------------------------------------------------------------------------
# Governance: group-based and combined gates (admissions roles)
# ---------------------------------------------------------------------------
class HasAnyGroupMixin(UserPassesTestMixin):
    """Pass if the user is in ANY of `required_groups`, or is a superuser.
    Complements RoleRequiredMixin — use when access is delegated via
    Django Groups (Registry Clerk, HR Officer, Head Teacher) rather than
    via `User.role`."""
    required_groups = []
    raise_exception = True

    def test_func(self):
        u = self.request.user
        if not u.is_authenticated:
            return False
        if u.is_superuser:
            return True
        return u.groups.filter(name__in=self.required_groups).exists()

    def handle_no_permission(self):
        _log_denied(self.request, self.required_groups)
        return super().handle_no_permission()


class AnyOfMixin(UserPassesTestMixin):
    """Pass if the user matches EITHER the roles OR the groups list.
    Convenience for views accessible to both, e.g. Head Teacher OR admin."""
    allowed_roles = []
    required_groups = []
    raise_exception = True

    def test_func(self):
        u = self.request.user
        if not u.is_authenticated:
            return False
        if u.is_superuser:
            return True
        if u.role in self.allowed_roles:
            return True
        return u.groups.filter(name__in=self.required_groups).exists()

    def handle_no_permission(self):
        _log_denied(self.request, self.allowed_roles + self.required_groups)
        return super().handle_no_permission()