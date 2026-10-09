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
    """Custom user with a role used across the whole ERP for RBAC.

    Governance extension ("Who Should Create Accounts?"):
      - `created_by` / `approved_by` record the creator and approver of
        every account, alongside the AuditLog entry.
      - `activated_at` marks when the account finished claiming/verification.
      - `two_factor_enabled` is required for admin/bursar/auditor accounts.
      - `must_change_password` forces a reset on next login for accounts
        created by invitation where the school wants the user to re-key.
    """

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

    # ------------------------------------------------------------------
    # Governance fields (doc §1, §9)
    # ------------------------------------------------------------------
    created_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='accounts_created',
        help_text=(
            'Who created this account (Registry Clerk, HR Officer, Head Teacher, '
            'or self for parent self-registration).'
        ),
    )
    approved_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='accounts_approved',
        help_text=(
            'Who approved this account (Head Teacher for teacher/staff; '
            'null for implicit approvals).'
        ),
    )
    activated_at = models.DateTimeField(null=True, blank=True)
    two_factor_enabled = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=False)

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

    class Meta(AbstractUser.Meta):
        abstract = False
        permissions = [
            # Master gate — required in addition to the specific permission.
            ('create_account', 'Can create user accounts'),
            # Purpose-scoped permissions matching InvitationToken.Purpose.
            ('create_student_account', 'Can create Student accounts'),
            ('create_parent_account', 'Can create Parent accounts'),
            ('create_teacher_account', 'Can create Teacher accounts'),
            ('create_staff_account', 'Can create Staff accounts'),
            ('create_admin_account', 'Can create Administrator accounts'),
            ('create_bursar_account', 'Can create Bursar/Accountant accounts'),
            ('create_auditor_account', 'Can create External Auditor accounts'),
            # Extra gate for admin / bursar / auditor accounts (doc §5).
            ('create_high_privilege_account',
             'Can create high-privilege accounts (admin/bursar/auditor)'),
            # Approval workflow.
            ('approve_account_creation',
             'Can approve pending account-creation requests'),
        ]


class PasswordHistory(models.Model):
    """AC-15: stores past password hashes so they can't be reused."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_history')
    password_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Password histories'


class AuditLog(models.Model):
    """AC-28 plus governance doc §9: every account lifecycle event, with a
    structured actor / target / method / reason / ip tuple."""

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
        # Governance lifecycle (doc §4, §5, §9)
        INVITATION_SENT = 'invitation_sent', 'Invitation Sent'
        INVITATION_CLAIMED = 'invitation_claimed', 'Invitation Claimed'
        INVITATION_REVOKED = 'invitation_revoked', 'Invitation Revoked'
        INVITATION_EXPIRED = 'invitation_expired', 'Invitation Expired'
        APPROVAL_REQUESTED = 'approval_requested', 'Approval Requested'
        APPROVAL_GRANTED = 'approval_granted', 'Approval Granted'
        APPROVAL_REJECTED = 'approval_rejected', 'Approval Rejected'
        # Teachers app: TCM compliance
        TCM_REMINDER_SENT = 'tcm_reminder_sent', 'TCM License Reminder Sent'

    class Method(models.TextChoices):
        INVITATION = 'invitation', 'Invitation'
        DIRECT = 'direct', 'Direct Creation'
        IMPORT = 'import', 'Bulk Import'
        SELF_REGISTRATION = 'self_registration', 'Self-Registration'

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='audit_logs',
    )
    # Governance: the account being acted upon when it isn't the actor.
    target_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='audit_logs_targeting_me',
    )
    username_attempted = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=25, choices=Action.choices)
    method = models.CharField(max_length=20, choices=Method.choices, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    detail = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        who = self.user or self.username_attempted or 'unknown'
        return f'{who} - {self.action} - {self.created_at:%Y-%m-%d %H:%M}'


class InvitationToken(models.Model):
    """Governance doc §4: a single-use, time-limited link sent by SMS/email
    that lets the recipient claim an account the school has already created
    a record for. Never a self-service signup — the record always exists
    first.

    One token = one real-world person, one account. For a student admission
    the Registry Clerk issues two tokens: one for the student account
    (delivered to the guardian phone, since the student is a minor), and
    one for the parent's own portal account.
    """

    class Purpose(models.TextChoices):
        STUDENT = 'student', 'Student Account'
        PARENT = 'parent', 'Parent / Guardian Account'
        TEACHER = 'teacher', 'Teacher Account'
        STAFF = 'staff', 'Non-teaching Staff Account'
        ADMIN = 'admin', 'Administrator Account'
        BURSAR = 'bursar', 'Bursar / Accountant Account'
        AUDITOR = 'auditor', 'External Auditor Account'

    class DeliveryMethod(models.TextChoices):
        SMS = 'sms', 'SMS'
        EMAIL = 'email', 'Email'
        BOTH = 'both', 'SMS + Email'
        MANUAL = 'manual', 'Manual (printed claim sheet)'

    token = models.CharField(max_length=64, unique=True, default=generate_verification_token)
    purpose = models.CharField(max_length=20, choices=Purpose.choices)

    # --- The record this invitation is anchored to (doc §1: records first) ---
    student = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE, null=True, blank=True,
        related_name='invitation_tokens',
    )
    teacher = models.ForeignKey(
        'teachers.Teacher', on_delete=models.CASCADE, null=True, blank=True,
        related_name='invitation_tokens',
    )
    staff = models.ForeignKey(
        'staff.StaffMember', on_delete=models.CASCADE, null=True, blank=True,
        related_name='invitation_tokens',
    )

    # --- Who this invitation is for (pre-fills the created User) ---
    proposed_username = models.CharField(max_length=150, blank=True)
    invited_first_name = models.CharField(max_length=150, blank=True)
    invited_last_name = models.CharField(max_length=150, blank=True)
    invited_email = models.EmailField(blank=True)
    invited_phone = models.CharField(max_length=20, blank=True)

    # --- Provenance & approval chain (doc §9) ---
    issued_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='invitations_issued',
    )
    approved_by = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, blank=True,
        related_name='invitations_approved',
    )
    reason = models.CharField(max_length=255, blank=True)

    # --- Lifecycle ---
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    delivered_at = models.DateTimeField(null=True, blank=True)
    delivery_method = models.CharField(
        max_length=10, choices=DeliveryMethod.choices, blank=True,
    )
    claimed_at = models.DateTimeField(null=True, blank=True)
    claimed_user = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='invitation_that_created_me',
    )
    used = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='invitations_revoked',
    )

    DEFAULT_VALIDITY_DAYS = 7

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['purpose']),
            models.Index(fields=['used', 'expires_at']),
        ]

    def __str__(self):
        who = self.invited_phone or self.invited_email or self.proposed_username or '—'
        return f'[{self.get_purpose_display()}] {who} ({"used" if self.used else "active"})'

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------
    def is_valid(self):
        return (
            not self.used
            and self.revoked_at is None
            and timezone.now() < self.expires_at
        )

    def revoke(self, revoked_by, reason=''):
        self.revoked_at = timezone.now()
        self.revoked_by = revoked_by
        self.save(update_fields=['revoked_at', 'revoked_by'])
        AuditLog.objects.create(
            user=revoked_by,
            target_user=self.claimed_user,
            action=AuditLog.Action.INVITATION_REVOKED,
            method=AuditLog.Method.INVITATION,
            reason=reason or f'Revoked {self.purpose} invitation',
            username_attempted=self.proposed_username or self.invited_phone,
        )

    def purpose_to_role(self):
        """Map invitation purpose → User.Role for the account we'll create."""
        mapping = {
            self.Purpose.STUDENT: User.Role.STUDENT,
            self.Purpose.PARENT: User.Role.PARENT,
            self.Purpose.TEACHER: User.Role.TEACHER,
            self.Purpose.STAFF: User.Role.STAFF,
            self.Purpose.ADMIN: User.Role.ADMIN,
            self.Purpose.BURSAR: User.Role.STAFF,   # bursar is staff + sub-role
            self.Purpose.AUDITOR: User.Role.STAFF,  # auditor is read-only staff
        }
        return mapping[self.purpose]

    @classmethod
    def issue(
        cls,
        *,
        purpose,
        issued_by,
        proposed_username='',
        invited_first_name='',
        invited_last_name='',
        invited_email='',
        invited_phone='',
        student=None,
        teacher=None,
        staff=None,
        approved_by=None,
        reason='',
        validity_days=None,
    ):
        validity_days = validity_days or cls.DEFAULT_VALIDITY_DAYS
        return cls.objects.create(
            purpose=purpose,
            issued_by=issued_by,
            approved_by=approved_by,
            proposed_username=proposed_username,
            invited_first_name=invited_first_name,
            invited_last_name=invited_last_name,
            invited_email=invited_email,
            invited_phone=invited_phone,
            student=student,
            teacher=teacher,
            staff=staff,
            reason=reason,
            expires_at=timezone.now() + datetime.timedelta(days=validity_days),
        )


class ApprovalRequest(models.Model):
    """Governance doc §5: teacher / non-teaching staff account creation is a
    two-step workflow — HR Officer drafts, Head Teacher approves, then the
    system issues the invitation. This model holds the draft.

    Admins/bursars/auditors use a three-step flow (direct create + 2FA +
    cool-off) and don't go through this model; they are created directly
    by the Head Teacher.
    """

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        SENT = 'sent', 'Invitation Sent'
        CANCELLED = 'cancelled', 'Cancelled'

    class Purpose(models.TextChoices):
        TEACHER = 'teacher', 'Teacher Account'
        STAFF = 'staff', 'Non-teaching Staff Account'

    purpose = models.CharField(max_length=20, choices=Purpose.choices)

    proposed_username = models.CharField(max_length=150)
    proposed_first_name = models.CharField(max_length=150, blank=True)
    proposed_last_name = models.CharField(max_length=150, blank=True)
    proposed_email = models.EmailField(blank=True)
    proposed_phone = models.CharField(max_length=20)

    teacher_record = models.ForeignKey(
        'teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approval_requests',
    )
    staff_record = models.ForeignKey(
        'staff.StaffMember', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approval_requests',
    )

    reason = models.CharField(max_length=255)

    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='approval_requests_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    decided_by = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, blank=True,
        related_name='approval_requests_decided',
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_notes = models.TextField(blank=True)

    invitation = models.OneToOneField(
        InvitationToken, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approval_request',
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['status'])]

    def __str__(self):
        return f'[{self.get_purpose_display()}] {self.proposed_username} ({self.status})'


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