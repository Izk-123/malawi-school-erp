"""
Attendance business logic, kept separate from views for testability
(per the attendance app's maintainability requirement).

Covers: roster lookup, bulk save (bulk_create/bulk_update for
performance), date-window validation, and stats aggregation used by the
history/summary/dashboard-widget views.
"""
import datetime

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.conf import settings as dj_settings
from django.utils import timezone

from students.models import Student
from .models import AttendanceRecord, is_school_day


def get_roster(class_name, stream):
    """AT-15: current enrollment for a class/stream, in a stable order."""
    return Student.objects.filter(class_name=class_name, stream=stream).order_by('full_name')


def validate_date_allowed(date, user):
    """AT-16: no future dates; teachers can't mark further back than the
    configured limit (admins/superusers are exempt)."""
    if date > datetime.date.today():
        raise ValidationError('Attendance cannot be marked for a future date.')
    is_admin = user.is_superuser or getattr(user, 'role', None) == 'admin'
    if not is_admin:
        limit = datetime.timedelta(days=getattr(dj_settings, 'ATTENDANCE_PAST_LIMIT_DAYS', 7))
        if (datetime.date.today() - date) > limit:
            raise ValidationError(
                f'Attendance for dates older than {limit.days} days can only be edited by an administrator.'
            )


@transaction.atomic
def save_bulk_attendance(class_name, stream, date, marks, user, period=''):
    """
    AT-01/AT-03/AT-24: save a roster's worth of attendance in one go.
    `marks` is {student_id: status}. Uses bulk_create/bulk_update rather
    than one query per student (NFR: <1s for 50 students).

    Returns (saved_records, skipped_locked_ids) - skipped_locked_ids are
    records that existed, differ from a non-admin user's edit window, and
    were therefore left untouched (AT-04/AT-16 immutability).
    """
    validate_date_allowed(date, user)

    students = {s.id: s for s in get_roster(class_name, stream) if s.id in marks}
    existing = {
        r.student_id: r for r in AttendanceRecord.objects.filter(
            student_id__in=students.keys(), date=date, period=period
        )
    }

    is_admin = user.is_superuser or getattr(user, 'role', None) == 'admin'
    to_create, to_update, skipped_locked_ids, touched_ids = [], [], [], []

    for student_id, status in marks.items():
        student = students.get(student_id)
        if not student:
            continue
        record = existing.get(student_id)
        if record:
            if not is_admin and not record.is_editable:
                skipped_locked_ids.append(record.id)
                continue
            if record.status != status:
                record.status = status
                record.marked_by = user
                to_update.append(record)
            touched_ids.append(record.id)
        else:
            new_record = AttendanceRecord(
                student=student, date=date, status=status, period=period,
                marked_by=user, class_name_at_time=student.class_name, stream_at_time=student.stream,
            )
            to_create.append(new_record)

    created = AttendanceRecord.objects.bulk_create(to_create)
    if to_update:
        AttendanceRecord.objects.bulk_update(to_update, ['status', 'marked_by', 'updated_at'])

    touched_ids.extend(r.id for r in created)
    touched_ids.extend(r.id for r in to_update)

    for student_id in {r.student_id for r in created} | {r.student_id for r in to_update}:
        students[student_id].recompute_attendance()

    return touched_ids, skipped_locked_ids


def mark_all_present(class_name, stream, date, user, period=''):
    """AT-03/AT-24: one-click 'mark everyone present', skipping students
    who already have a record for that date so it never overwrites an
    exception (e.g. someone already marked absent)."""
    validate_date_allowed(date, user)
    roster = get_roster(class_name, stream)
    already_marked = set(
        AttendanceRecord.objects.filter(
            student__in=roster, date=date, period=period
        ).values_list('student_id', flat=True)
    )
    to_create = [
        AttendanceRecord(
            student=s, date=date, status=AttendanceRecord.Status.PRESENT, period=period,
            marked_by=user, class_name_at_time=s.class_name, stream_at_time=s.stream,
        )
        for s in roster if s.id not in already_marked
    ]
    created = AttendanceRecord.objects.bulk_create(to_create)
    for record in created:
        record.student.recompute_attendance()
    return len(created)


def undo_records(record_ids, user):
    """Usability NFR: 'undo last action' - reverts each touched record to
    its previous historical version, or deletes it if it was newly created."""
    reverted, deleted = 0, 0
    for record in AttendanceRecord.objects.filter(id__in=record_ids):
        history_qs = record.history.all().order_by('-history_date')
        if history_qs.count() <= 1:
            record.delete()
            deleted += 1
            continue
        previous = history_qs[1]
        record.status = previous.status
        record.save()
        reverted += 1
        record.student.recompute_attendance()
    return reverted, deleted


def compute_stats(queryset):
    """AT-12: percentage present, absence count, lateness count for a
    given AttendanceRecord queryset (e.g. one student over a date range,
    or a whole class on one day)."""
    total = queryset.count()
    if not total:
        return {'total': 0, 'present': 0, 'absent': 0, 'late': 0, 'percentage_present': 0}
    present = queryset.filter(status=AttendanceRecord.Status.PRESENT).count()
    absent = queryset.filter(status=AttendanceRecord.Status.ABSENT).count()
    late = queryset.filter(status=AttendanceRecord.Status.LATE).count()
    return {
        'total': total,
        'present': present,
        'absent': absent,
        'late': late,
        'percentage_present': round((present + late) / total * 100, 1),
    }


def todays_school_wide_percentage():
    """AT-13: dashboard widget - today's overall attendance percentage
    across every record taken today (not the per-student running average)."""
    today = datetime.date.today()
    if not is_school_day(today):
        return None
    stats = compute_stats(AttendanceRecord.objects.filter(date=today))
    return stats['percentage_present'] if stats['total'] else None
