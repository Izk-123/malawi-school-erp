import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords


class Holiday(models.Model):
    """AT-17: non-school days excluded from attendance marking/reporting."""
    date = models.DateField(unique=True)
    name = models.CharField(max_length=150)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f'{self.date} - {self.name}'


def is_school_day(date):
    """AT-17: weekends and declared holidays are not marked."""
    if date.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    return not Holiday.objects.filter(date=date).exists()


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'present', 'Present'
        ABSENT = 'absent', 'Absent'
        LATE = 'late', 'Late'

    student = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE, related_name='attendance_records'
    )
    date = models.DateField(db_index=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PRESENT)
    # AT-06/SY-29: optional per-period recording; blank means daily-level
    # attendance. syllabus_subject additionally allows subject-specific
    # absence-pattern reporting (e.g. "40% of Physics periods missed").
    period = models.CharField(max_length=50, blank=True)
    syllabus_subject = models.ForeignKey(
        'syllabus.Subject', on_delete=models.SET_NULL, null=True, blank=True, related_name='attendance_records',
    )
    # AT-14: snapshot of the class/stream *at the time attendance was taken*,
    # so historical reports stay accurate even if a student is later promoted
    # or transferred to a different class/stream.
    class_name_at_time = models.CharField(max_length=10, blank=True)
    stream_at_time = models.CharField(max_length=1, blank=True)
    # AT-22: who marked it, and when (separate from `date`, which is the
    # attendance date, not the timestamp of the marking action).
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='attendance_marked',
    )
    marked_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        unique_together = ('student', 'date', 'period')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['class_name_at_time', 'stream_at_time', 'date']),
        ]

    def __str__(self):
        return f'{self.student.full_name} - {self.date} - {self.status}'

    def clean(self):
        # AT-16: no marking ahead of time.
        if self.date and self.date > datetime.date.today():
            raise ValidationError('Attendance cannot be marked for a future date.')

    def save(self, *args, **kwargs):
        if not self.class_name_at_time:
            self.class_name_at_time = self.student.class_name
        if not self.stream_at_time:
            self.stream_at_time = self.student.stream
        super().save(*args, **kwargs)

    @property
    def is_editable(self):
        """AT-04: teachers can correct same-day mistakes within a configurable
        window; AT-16 additionally blocks edits to attendance dates further
        back than a configurable limit. Admins bypass both via the view layer."""
        from django.conf import settings as dj_settings
        window = datetime.timedelta(hours=getattr(dj_settings, 'ATTENDANCE_EDIT_WINDOW_HOURS', 24))
        past_limit = datetime.timedelta(days=getattr(dj_settings, 'ATTENDANCE_PAST_LIMIT_DAYS', 7))
        now = timezone.now()
        within_marking_window = (now - self.marked_at) <= window
        within_past_limit = (datetime.date.today() - self.date) <= past_limit
        return within_marking_window and within_past_limit
