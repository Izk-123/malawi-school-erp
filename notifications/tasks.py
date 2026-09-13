"""
Celery background tasks for the ERP.

In development, CELERY_TASK_ALWAYS_EAGER=True (see settings.py) means
`.delay(...)` calls run synchronously in-process -- no broker or worker
needed on Windows to try this out. Flip that flag off and run:

    celery -A config worker --pool=solo --loglevel=info

once you have Redis available, to get true async background execution.
"""
import logging

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

from .models import Notification
from .services import push_notification

logger = logging.getLogger(__name__)


def _send_sms_stub(phone_number, message):
    """
    Placeholder for an Africa's Talking / Twilio integration.
    Wire this up to the real SDK when credentials are available; for now
    it just logs, so the rest of the pipeline (Notification row + Channels
    push) can be exercised end-to-end without external services.
    """
    logger.info('[SMS STUB] to=%s message=%s', phone_number, message)


@shared_task
def send_fee_reminder(student_id):
    from students.models import Student
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return
    message = (
        f'Reminder: {student.full_name} has an outstanding fee balance of '
        f'MK {student.balance:,.2f}.'
    )
    _send_sms_stub(student.guardian_phone, message)
    for guardian in student.guardians.all():
        push_notification(guardian, message, Notification.NotificationType.FEE_DUE)
    if student.user:
        push_notification(student.user, message, Notification.NotificationType.FEE_DUE)


@shared_task
def notify_absence(student_id, date):
    """AT-18: notify guardians immediately when a student is marked absent."""
    from students.models import Student
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return
    message = f'{student.full_name} was marked absent on {date}.'
    _send_sms_stub(student.guardian_phone, message)
    for guardian in student.guardians.all():
        push_notification(guardian, message, Notification.NotificationType.LOW_ATTENDANCE)


@shared_task
def notify_low_attendance(student_id):
    from students.models import Student
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return
    message = (
        f'{student.full_name}\'s attendance has dropped to '
        f'{student.attendance_percentage}%.'
    )
    _send_sms_stub(student.guardian_phone, message)
    for guardian in student.guardians.all():
        push_notification(guardian, message, Notification.NotificationType.LOW_ATTENDANCE)


@shared_task
def notify_grade_published(grade_record_id):
    from grades.models import GradeRecord
    try:
        record = GradeRecord.objects.select_related('student').get(id=grade_record_id)
    except GradeRecord.DoesNotExist:
        return
    student = record.student
    message = f'New grade published: {record.subject} ({record.exam}) - {record.score}% ({record.grade}).'
    if student.user:
        push_notification(student.user, message, Notification.NotificationType.GRADE_PUBLISHED)
    for guardian in student.guardians.all():
        push_notification(guardian, message, Notification.NotificationType.GRADE_PUBLISHED)


@shared_task
def send_bulk_announcement(user_ids, message):
    from accounts.models import User
    for user in User.objects.filter(id__in=user_ids):
        push_notification(user, message, Notification.NotificationType.ANNOUNCEMENT)


@shared_task
def notify_admins_missing_data(student_id, message):
    """ST-34: alert every admin user when important student data is missing."""
    from accounts.models import User
    for admin_user in User.objects.filter(role=User.Role.ADMIN, is_active=True):
        push_notification(admin_user, message, Notification.NotificationType.ANNOUNCEMENT)


@shared_task
def send_account_event_notification(user_id, event):
    """AC-29/AC-05: notify a user about critical account events
    (activation/deactivation, and - reused for welcome messages -
    account creation)."""
    from accounts.models import User
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return
    messages_by_event = {
        'activated': 'Your account has been reactivated by the school administrator.',
        'deactivated': 'Your account has been deactivated. Contact the school office for help.',
        'created': f'Welcome to the Malawi School ERP, {user.get_full_name() or user.username}! Your account is ready.',
        'locked': 'Your account was locked after too many failed login attempts. Contact an administrator to unlock it.',
    }
    message = messages_by_event.get(event, 'There has been an update to your account.')
    _send_sms_stub(user.phone_number, message)
    push_notification(user, message, Notification.NotificationType.ANNOUNCEMENT)
