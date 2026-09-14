from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime
import re
import secrets


def generate_verification_token():
    return secrets.token_urlsafe(32)


def malawi_phone_validator(value):
    """Accepts +265XXXXXXXXX with or without spaces (e.g. '+265 991 234 567')."""
    digits_only = re.sub(r'\s+', '', value or '')
    if not re.match(r'^\+265\d{9}$', digits_only):
        raise ValidationError(
            'Phone number must be in the Malawian format +265XXXXXXXXX (spaces allowed).',
            code='invalid_malawi_phone',
        )


class User(AbstractUser):
    """Custom user with a role used across the whole ERP for RBAC."""

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrator'
        TEACHER = 'teacher', 'Teacher'
        STUDENT = 'student', 'Student'
        PARENT = 'parent', 'Parent'
        STAFF = 'staff', 'Staff'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    preferred_language = models.CharField(
        max_length=10,
        choices=[('en', 'English'), ('ny', 'Chichewa')],
        default='en',
    )
    # AC-07c: verified email/phone, tracked per account. Defaults to True
    # so admin-created accounts and seed data aren't retroactively locked
    # out; only the self-registration flow (AC-02) sets these False and
    # actually walks a person through verification.
    email_verified = models.BooleanField(default=True)
    phone_verified = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    @property
    def is_teacher_role(self):
        return self.role == self.Role.TEACHER

    @property
    def is_student_role(self):
        return self.role == self.Role.STUDENT

    @property
    def is_parent_role(self):
        return self.role == self.Role.PARENT

    @property
    def is_staff_role(self):
        return self.role == self.Role.STAFF


class PasswordHistory(models.Model):
    """AC-15: stores past password hashes so they can't be reused."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_history')
    password_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Password histories'


class AuditLog(models.Model):
    """AC-28: records authentication events (login, logout, failed login,
    password change) plus account lifecycle events (activate/deactivate)."""

    class Action(models.TextChoices):
        LOGIN_SUCCESS = 'login_success', 'Login Success'
        LOGIN_FAILED = 'login_failed', 'Login Failed'
        LOGOUT = 'logout', 'Logout'
        PASSWORD_CHANGED = 'password_changed', 'Password Changed'
        PASSWORD_RESET = 'password_reset', 'Password Reset'
        ACCOUNT_LOCKED = 'account_locked', 'Account Locked'
        ACCOUNT_UNLOCKED = 'account_unlocked', 'Account Unlocked'
        ACCOUNT_ACTIVATED = 'account_activated', 'Account Activated'
        ACCOUNT_DEACTIVATED = 'account_deactivated', 'Account Deactivated'
        ACCOUNT_CREATED = 'account_created', 'Account Created'
        PERMISSION_DENIED = 'permission_denied', 'Permission Denied'

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    username_attempted = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=25, choices=Action.choices)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    detail = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        who = self.user or self.username_attempted or 'unknown'
        return f'{who} - {self.action} - {self.created_at:%Y-%m-%d %H:%M}'


class EmailVerificationToken(models.Model):
    """AC-07c/e: single-use email verification link, expires in 24h."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verification_tokens')
    token = models.CharField(max_length=64, unique=True, default=generate_verification_token)
    created_at = models.DateTimeField(default=timezone.now)
    used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.used and (timezone.now() - self.created_at) < datetime.timedelta(hours=24)

    def __str__(self):
        return f'Email token for {self.user} ({"used" if self.used else "active"})'


class PhoneOTP(models.Model):
    """AC-07c/e: 6-digit phone OTP, expires in 10 minutes, max 5 attempts."""
    MAX_ATTEMPTS = 5

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phone_otps')
    phone_number = models.CharField(max_length=20)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)

    def is_valid(self):
        return (
            not self.used and self.attempts < self.MAX_ATTEMPTS
            and (timezone.now() - self.created_at) < datetime.timedelta(minutes=10)
        )

    def __str__(self):
        return f'OTP for {self.user} -> {self.phone_number}'
