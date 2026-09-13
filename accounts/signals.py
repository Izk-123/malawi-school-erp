"""
AC-16: keep a Django Group in sync with each user's role field.
AC-28: log authentication events (login/logout/failed login/password change)
        plus account lockouts raised by django-axes.
"""
from django.contrib.auth.models import Group
from django.contrib.auth.signals import (
    user_logged_in, user_logged_out, user_login_failed,
)
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, AuditLog, PasswordHistory

try:
    from axes.signals import user_locked_out
except ImportError:  # pragma: no cover - axes always installed, defensive only
    user_locked_out = None


def _client_ip(request):
    if not request:
        return None
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@receiver(post_save, sender=User)
def sync_role_group(sender, instance, **kwargs):
    """AC-16/17: every user belongs to exactly one role Group, which the
    `assign_role_permissions` management command grants model permissions to."""
    group, _ = Group.objects.get_or_create(name=instance.role)
    instance.groups.set([group])


@receiver(user_logged_in)
def log_login_success(sender, request, user, **kwargs):
    AuditLog.objects.create(
        user=user, action=AuditLog.Action.LOGIN_SUCCESS,
        ip_address=_client_ip(request), username_attempted=user.username,
    )


@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    if user is None:
        return
    AuditLog.objects.create(
        user=user, action=AuditLog.Action.LOGOUT,
        ip_address=_client_ip(request), username_attempted=user.username,
    )


@receiver(user_login_failed)
def log_login_failed(sender, credentials, request=None, **kwargs):
    AuditLog.objects.create(
        user=None, action=AuditLog.Action.LOGIN_FAILED,
        ip_address=_client_ip(request), username_attempted=credentials.get('username', ''),
    )


if user_locked_out is not None:
    @receiver(user_locked_out)
    def log_account_locked(sender, request, username, ip_address=None, **kwargs):
        AuditLog.objects.create(
            user=None, action=AuditLog.Action.ACCOUNT_LOCKED,
            ip_address=ip_address or _client_ip(request), username_attempted=username or '',
            detail='Locked after repeated failed login attempts.',
        )


def record_password_history(user, raw_password):
    """Call after setting a new password so PasswordHistoryValidator can
    check future changes against it (AC-15), and log the change (AC-28)."""
    PasswordHistory.objects.create(user=user, password_hash=user.password)
    AuditLog.objects.create(user=user, action=AuditLog.Action.PASSWORD_CHANGED, username_attempted=user.username)
    # Trim to the last 10 entries so the table doesn't grow unbounded.
    ids_to_keep = PasswordHistory.objects.filter(user=user).order_by('-created_at').values_list('id', flat=True)[:10]
    PasswordHistory.objects.filter(user=user).exclude(id__in=list(ids_to_keep)).delete()
