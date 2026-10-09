"""Celery tasks for the teachers app.

The only scheduled job here is the TCM license-expiry reminder sweep.
It is deliberately idempotent: it records each reminder as an
``AuditLog`` row keyed by ``(teacher, window)``, so running it more than
once a day — or replaying it manually — cannot double-notify a teacher
or double-count them in the HR digest.

``send_manual_tcm_reminder`` is the same logic, callable one teacher at a
time from the admin bulk action. It shares the dedupe key with the
automatic sweep so the two paths cannot double-message.
"""
import datetime
import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone

from .models import Teacher


logger = logging.getLogger(__name__)
User = get_user_model()


# Windows (in days) at which a teacher is warned before their TCM license
# expires. Iteration order in ``_applicable_window`` means the *tightest*
# window wins — a license 5 days out matches the 7-day window, not 60.
REMINDER_WINDOWS = (60, 30, 7)

# TCM statuses that mean "there is a live license to renew". Suspended
# and expired licenses are handled by the assignment-block path, not by
# a renewal nudge.
_RENEWABLE_STATUSES = (
    Teacher.TCMStatus.REGISTERED,
    Teacher.TCMStatus.PROVISIONAL,
)


# ---------------------------------------------------------------------------
# Daily sweep
# ---------------------------------------------------------------------------
@shared_task
def send_tcm_expiry_reminders():
    """Daily sweep: notify teachers whose TCM license is close to expiry.

    Returns ``{'reminders_sent': N}`` so a caller (management command,
    monitoring probe) can assert on it. Failures on individual channels
    are logged and swallowed; the task itself only raises if the DB query
    fails, which would be a genuine bug.
    """
    today = timezone.localdate()
    horizon = today + datetime.timedelta(days=max(REMINDER_WINDOWS))

    candidates = (
        Teacher.objects
        .filter(
            status=Teacher.Status.ACTIVE,
            tcm_status__in=_RENEWABLE_STATUSES,
            tcm_license_expiry__isnull=False,
            tcm_license_expiry__gte=today,
            tcm_license_expiry__lte=horizon,
        )
        .select_related('user')
        .order_by('tcm_license_expiry', 'pk')
    )

    sent = []  # list of (teacher, window, days_until_expiry)
    for teacher in candidates:
        days = (teacher.tcm_license_expiry - today).days
        window = _applicable_window(days)
        if window is None:
            # Shouldn't happen given the query filter, but be defensive.
            continue
        if _reminder_already_sent(teacher, window):
            continue

        dispatched = _send_teacher_reminder(teacher, days)
        if not dispatched:
            # Nothing reached the teacher — leave no audit row so
            # tomorrow's sweep retries the same window.
            continue

        _record_reminder(teacher, window)
        sent.append((teacher, window, days))

    if sent:
        _send_hr_digest(sent)

    logger.info('TCM sweep: %d reminder(s) sent', len(sent))
    return {'reminders_sent': len(sent)}


# ---------------------------------------------------------------------------
# Manual, single-teacher trigger (used by TeacherAdmin bulk action)
# ---------------------------------------------------------------------------
def send_manual_tcm_reminder(teacher):
    """Send one reminder to ``teacher`` outside the daily sweep.

    Returns one of:
      ``'sent'``    — a channel accepted the message and the audit row
                      was written.
      ``'skipped'`` — the teacher's status isn't renewable, their license
                      isn't within any reminder window, or a reminder for
                      the applicable window has already been recorded
                      (whether by the automatic sweep or a previous
                      manual send).
      ``'failed'``  — every channel raised; nothing was recorded, so the
                      next sweep will retry.

    Not a Celery task — called synchronously from the admin action so the
    admin gets an immediate per-teacher verdict.
    """
    if teacher.tcm_status not in _RENEWABLE_STATUSES:
        return 'skipped'

    days = teacher.tcm_days_until_expiry
    if days is None or days < 0:
        # No expiry on file, or already past — both handled elsewhere
        # (the assignment-block path), not by a renewal nudge.
        return 'skipped'

    window = _applicable_window(days)
    if window is None:
        # Outside every reminder window. Sending anyway would be noise;
        # admin can widen REMINDER_WINDOWS if they want earlier nudges.
        return 'skipped'

    if _reminder_already_sent(teacher, window):
        return 'skipped'

    dispatched = _send_teacher_reminder(teacher, days)
    if not dispatched:
        return 'failed'

    _record_reminder(teacher, window)
    return 'sent'


# ---------------------------------------------------------------------------
# Window selection
# ---------------------------------------------------------------------------
def _applicable_window(days_until_expiry):
    """Return the tightest reminder window that applies, or ``None``.

    Iterating ascending (7, 30, 60) means the first match is the window
    closest to expiry. A license 25 days out returns 30 (not 60); a
    license 5 days out returns 7; a license 90 days out returns ``None``.
    """
    for window in sorted(REMINDER_WINDOWS):
        if days_until_expiry <= window:
            return window
    return None


# ---------------------------------------------------------------------------
# Idempotency — AuditLog-backed
# ---------------------------------------------------------------------------
def _reminder_key(teacher, window):
    """Stable, queryable key for one (teacher, window) reminder.

    Kept short so it fits comfortably in ``AuditLog.detail`` (max 255).
    """
    return f'tcm-reminder:{window}d:{teacher.pk}'


def _reminder_already_sent(teacher, window):
    from accounts.models import AuditLog
    return AuditLog.objects.filter(
        action=AuditLog.Action.TCM_REMINDER_SENT,
        detail=_reminder_key(teacher, window),
    ).exists()


def _record_reminder(teacher, window):
    from accounts.models import AuditLog
    AuditLog.objects.create(
        user=None,  # system-initiated: no actor
        target_user=teacher.user,
        action=AuditLog.Action.TCM_REMINDER_SENT,
        reason=(
            f'TCM license for {teacher.full_name} '
            f'({teacher.teacher_id}) expires on {teacher.tcm_license_expiry}.'
        ),
        detail=_reminder_key(teacher, window),
    )


# ---------------------------------------------------------------------------
# Per-teacher dispatch
# ---------------------------------------------------------------------------
def _send_teacher_reminder(teacher, days_until_expiry):
    """Send one reminder via every available channel.

    Returns ``True`` if at least one channel accepted the message, so the
    caller knows whether to record the reminder. SMS goes through the
    notifications app (which owns retry/throttling); email is sent
    synchronously inside this task because we are already on a worker.
    """
    first_name = (teacher.full_name or '').split(' ', 1)[0] or 'there'
    expiry = teacher.tcm_license_expiry
    plural = '' if days_until_expiry == 1 else 's'

    sms_body = (
        f'{first_name}, your TCM teaching license expires in '
        f'{days_until_expiry} day{plural} '
        f'on {expiry:%d %b %Y}. Please renew at the Teaching Council of '
        f'Malawi to remain eligible for class assignment.'
    )
    email_body = (
        f'Dear {teacher.full_name},\n\n'
        f'Your Teaching Council of Malawi (TCM) license (number '
        f'{teacher.tcm_registration_number}) expires in '
        f'{days_until_expiry} day{plural} '
        f'on {expiry:%d %b %Y}.\n\n'
        f'A teacher without a valid TCM license cannot be assigned to a '
        f'class. Please renew at the Teaching Council of Malawi and upload '
        f'the new certificate to your profile so the school can update its '
        f'records.\n\n'
        f'— Mzuzu Secondary School'
    )

    dispatched = False

    if teacher.phone_number:
        try:
            from notifications.tasks import send_sms
            send_sms.delay(teacher.phone_number, sms_body)
            dispatched = True
        except Exception:
            logger.exception(
                'TCM SMS reminder failed for teacher pk=%s', teacher.pk,
            )

    if teacher.email:
        try:
            send_mail(
                subject=f'TCM license expiring in {days_until_expiry} day{plural}',
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[teacher.email],
                fail_silently=False,
            )
            dispatched = True
        except Exception:
            logger.exception(
                'TCM email reminder failed for teacher pk=%s', teacher.pk,
            )

    return dispatched


# ---------------------------------------------------------------------------
# HR / Head Teacher digest
# ---------------------------------------------------------------------------
def _send_hr_digest(sent):
    """One summary email per sweep to HR / Head Teacher / admins.

    ``sent`` is a list of ``(teacher, window, days_until_expiry)`` tuples
    from the sweep above.
    """
    recipients = _hr_recipients()
    if not recipients:
        logger.warning(
            'TCM sweep: %d reminder(s) sent but no HR/Head Teacher/admin '
            'recipients with an email address — digest skipped.', len(sent),
        )
        return

    lines = [f'{len(sent)} TCM license reminder(s) sent today:', '']
    for teacher, window, days in sent:
        plural = '' if days == 1 else 's'
        lines.append(
            f'  • {teacher.full_name} ({teacher.teacher_id}) — '
            f'expires in {days} day{plural} '
            f'({teacher.tcm_license_expiry:%d %b %Y}) '
            f'[{window}-day reminder]'
        )
    lines += [
        '',
        'Teachers without a valid TCM license cannot be assigned to a class.',
    ]

    try:
        send_mail(
            subject=f'TCM expiry: {len(sent)} reminder(s) sent',
            message='\n'.join(lines),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
        )
    except Exception:
        logger.exception('TCM HR digest email failed')


def _hr_recipients():
    """Email addresses for HR Officer / Head Teacher / admins.

    Matches on ``User.role == 'admin'`` (baseline) *or* membership of the
    ``hr_officer`` / ``head_teacher`` Django groups — the same delegation
    mechanism ``accounts.mixins.HasAnyGroupMixin`` uses.
    """
    qs = (
        User.objects
        .filter(is_active=True)
        .filter(
            Q(role=User.Role.ADMIN)
            | Q(groups__name__in=['hr_officer', 'head_teacher'])
        )
        .exclude(email='')
        .distinct()
    )
    return list(qs.values_list('email', flat=True))