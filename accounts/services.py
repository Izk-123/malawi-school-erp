"""Account-lifecycle services — governance doc enforcement.

Everything that creates, approves, or claims an account funnels through
here so that:
  - the permission check is one function (`can_create_account_for`),
  - the audit entry is written exactly once per event,
  - the invitation delivery is always queued via Celery,
  - the "records first, accounts second" rule is enforced structurally
    (`issue_invitation` refuses to run without a target record).
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from .constants import (
    APPROVE_ACCOUNT_CREATION,
    CREATE_ACCOUNT,
    CREATE_HIGH_PRIVILEGE_ACCOUNT,
    HIGH_PRIVILEGE_PURPOSES,
    INVITATION_PURPOSE_PERMISSION,
)
from .models import AuditLog, ApprovalRequest, InvitationToken, User


# ---------------------------------------------------------------------------
# Permission gate
# ---------------------------------------------------------------------------
def can_create_account_for(user, purpose: str) -> bool:
    """Return True iff `user` may issue an invitation / create an account
    of the given purpose.

    Rules (doc §2):
      * superuser       -> everything
      * must have `create_account`
      * must have the purpose-specific permission
      * admin/bursar/auditor additionally need `create_high_privilege_account`
    """
    if not user or not getattr(user, 'is_authenticated', False) or not user.is_active:
        return False
    if user.is_superuser:
        return True
    if not user.has_perm(CREATE_ACCOUNT):
        return False
    required = INVITATION_PURPOSE_PERMISSION.get(purpose)
    if not required or not user.has_perm(required):
        return False
    if purpose in HIGH_PRIVILEGE_PURPOSES and not user.has_perm(CREATE_HIGH_PRIVILEGE_ACCOUNT):
        return False
    return True


def can_approve_creations(user) -> bool:
    """Head Teacher (or superuser) may approve pending account requests."""
    return bool(
        user and user.is_authenticated and user.is_active
        and (user.is_superuser or user.has_perm(APPROVE_ACCOUNT_CREATION))
    )


# ---------------------------------------------------------------------------
# Invitation issuance
# ---------------------------------------------------------------------------
@transaction.atomic
def issue_invitation(
    *,
    purpose: str,
    issued_by: User,
    reason: str = '',
    approved_by: User | None = None,
    **kwargs,
) -> InvitationToken:
    """Issue + queue delivery of an invitation. Enforces the permission
    gate and writes the audit entry in one transaction.

    Extra kwargs are passed through to `InvitationToken.issue` (student,
    teacher, staff, invited_phone, invited_email, proposed_username, ...).
    """
    if not can_create_account_for(issued_by, purpose):
        AuditLog.objects.create(
            user=issued_by,
            action=AuditLog.Action.PERMISSION_DENIED,
            username_attempted=getattr(issued_by, 'username', ''),
            detail=f'Attempted to issue a {purpose} invitation without permission.',
        )
        raise PermissionDenied(f'Not allowed to create {purpose} accounts.')

    invitation = InvitationToken.issue(
        purpose=purpose, issued_by=issued_by, approved_by=approved_by,
        reason=reason, **kwargs,
    )

    AuditLog.objects.create(
        user=issued_by,
        action=AuditLog.Action.INVITATION_SENT,
        method=AuditLog.Method.INVITATION,
        reason=reason or f'{purpose} invitation issued',
        username_attempted=invitation.proposed_username or invitation.invited_phone,
        detail=f'Invitation {invitation.token[:8]}… purpose={purpose}',
    )

    # Delivery is async so a bulk import of 150 admissions doesn't block.
    from .tasks import deliver_invitation
    deliver_invitation.delay(invitation.id)

    return invitation


@transaction.atomic
def issue_admission_invitations(*, student, issued_by: User, reason: str = ''):
    """Convenience: on a student admission, issue BOTH the student's
    invitation (delivered to the guardian's phone, since the student is a
    minor) and the parent's own portal invitation.

    Returns (student_invitation, parent_invitation_or_None). The parent
    invitation is skipped if the student already has a linked guardian
    user whose phone matches.
    """
    guardian_phone = student.guardian_phone
    guardian_email = ''  # Student has no guardian_email field today

    student_inv = issue_invitation(
        purpose='student',
        issued_by=issued_by,
        student=student,
        proposed_username=student.student_id,
        invited_first_name=student.full_name.split(' ', 1)[0],
        invited_last_name=(student.full_name.split(' ', 1)[1] if ' ' in student.full_name else ''),
        invited_phone=guardian_phone,
        invited_email=guardian_email,
        reason=reason or f'Admission of {student.full_name} ({student.student_id})',
    )

    # Issue the parent's own invitation unless a matching parent user exists.
    parent_inv = None
    if guardian_phone:
        already = User.objects.filter(
            role=User.Role.PARENT, phone_number=guardian_phone,
        ).exists()
        if not already:
            parent_inv = issue_invitation(
                purpose='parent',
                issued_by=issued_by,
                student=student,
                invited_first_name=student.guardian_name.split(' ', 1)[0],
                invited_last_name=(student.guardian_name.split(' ', 1)[1]
                                   if ' ' in student.guardian_name else ''),
                invited_phone=guardian_phone,
                reason=f'Parent account for {student.full_name} ({student.student_id})',
            )

    return student_inv, parent_inv


@transaction.atomic
def claim_invitation(*, invitation: InvitationToken, raw_password: str,
                     request=None) -> User:
    """Turn an invitation into a live User account.

    Called from the claim view after the user has set a password. Enforces
    single-use, expiry, and audit-logged linkage to the target record.
    """
    if not invitation.is_valid():
        raise ValidationError('This invitation is no longer valid.')

    email_verified = bool(invitation.invited_email)
    phone_verified = bool(invitation.invited_phone)

    user = User(
        username=invitation.proposed_username or _derive_username(invitation),
        first_name=invitation.invited_first_name,
        last_name=invitation.invited_last_name,
        email=invitation.invited_email,
        phone_number=invitation.invited_phone,
        role=invitation.purpose_to_role(),
        created_by=invitation.issued_by,
        approved_by=invitation.approved_by,
        activated_at=timezone.now(),
        email_verified=email_verified,
        phone_verified=phone_verified,
    )
    user.set_password(raw_password)
    user.save()

    # Link back to the real-world record (doc §1: records first).
    if invitation.student_id:
        invitation.student.user = user
        invitation.student.save(update_fields=['user'])
    if invitation.teacher_id:
        invitation.teacher.user = user
        invitation.teacher.save(update_fields=['user'])
    if invitation.staff_id:
        invitation.staff.user = user
        invitation.staff.save(update_fields=['user'])

    invitation.used = True
    invitation.claimed_at = timezone.now()
    invitation.claimed_user = user
    invitation.save(update_fields=['used', 'claimed_at', 'claimed_user'])

    AuditLog.objects.create(
        user=user,
        target_user=user,
        action=AuditLog.Action.INVITATION_CLAIMED,
        method=AuditLog.Method.INVITATION,
        reason=invitation.reason or f'{invitation.purpose} invitation claimed',
        username_attempted=user.username,
        ip_address=_ip(request),
    )
    AuditLog.objects.create(
        user=invitation.issued_by,
        target_user=user,
        action=AuditLog.Action.ACCOUNT_CREATED,
        method=AuditLog.Method.INVITATION,
        reason=invitation.reason or f'{invitation.purpose} invitation claimed',
        username_attempted=user.username,
    )

    # Post-claim hooks: parent accounts link to the student automatically.
    if invitation.purpose == InvitationToken.Purpose.PARENT and invitation.student_id:
        invitation.student.guardians.add(user)
    if invitation.purpose == InvitationToken.Purpose.STUDENT and invitation.student_id:
        # Minor student: don't unlock anything yet beyond attendance/grades.
        pass

    return user


def _derive_username(invitation: InvitationToken) -> str:
    """Fallback username when the invitation didn't specify one."""
    base = (invitation.invited_phone or invitation.invited_email or 'user').strip()
    base = base.replace('+', '').replace('@', '_').replace('.', '_')
    candidate = base
    n = 1
    while User.objects.filter(username=candidate).exists():
        n += 1
        candidate = f'{base}_{n}'
    return candidate


def _ip(request):
    if request is None:
        return None
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# ---------------------------------------------------------------------------
# Approval workflow (doc §5: teacher / staff two-step)
# ---------------------------------------------------------------------------
@transaction.atomic
def create_approval_request(*, purpose, drafted_by, **fields) -> ApprovalRequest:
    """HR Officer drafts an account request; Head Teacher approves later."""
    if not can_create_account_for(drafted_by, purpose):
        raise PermissionDenied(f'Not allowed to draft {purpose} accounts.')
    request = ApprovalRequest.objects.create(
        purpose=purpose, created_by=drafted_by, **fields,
    )
    AuditLog.objects.create(
        user=drafted_by,
        action=AuditLog.Action.APPROVAL_REQUESTED,
        method=AuditLog.Method.INVITATION,
        reason=request.reason,
        username_attempted=request.proposed_username,
    )
    return request


@transaction.atomic
def decide_approval_request(*, request: ApprovalRequest, decided_by, approve: bool,
                            notes: str = ''):
    """Head Teacher approves or rejects a draft; approval issues the
    invitation in the same transaction."""
    if not can_approve_creations(decided_by):
        raise PermissionDenied('Only the Head Teacher may decide account requests.')
    if request.status != ApprovalRequest.Status.DRAFT:
        raise ValidationError('This request has already been decided.')

    request.decided_by = decided_by
    request.decided_at = timezone.now()
    request.decision_notes = notes

    if approve:
        request.status = ApprovalRequest.Status.APPROVED
        invitation = issue_invitation(
            purpose=request.purpose,
            issued_by=request.created_by,
            approved_by=decided_by,
            proposed_username=request.proposed_username,
            invited_first_name=request.proposed_first_name,
            invited_last_name=request.proposed_last_name,
            invited_email=request.proposed_email,
            invited_phone=request.proposed_phone,
            teacher=request.teacher_record,
            staff=request.staff_record,
            reason=request.reason,
        )
        request.invitation = invitation
        request.status = ApprovalRequest.Status.SENT
        AuditLog.objects.create(
            user=decided_by,
            action=AuditLog.Action.APPROVAL_GRANTED,
            method=AuditLog.Method.INVITATION,
            reason=notes or f'Approved {request.purpose} account for {request.proposed_username}',
            username_attempted=request.proposed_username,
        )
    else:
        request.status = ApprovalRequest.Status.REJECTED
        AuditLog.objects.create(
            user=decided_by,
            action=AuditLog.Action.APPROVAL_REJECTED,
            method=AuditLog.Method.INVITATION,
            reason=notes or f'Rejected {request.purpose} account for {request.proposed_username}',
            username_attempted=request.proposed_username,
        )

    request.save()
    return request