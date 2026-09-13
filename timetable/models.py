from django.core.exceptions import ValidationError
from django.db import models


class TimetablePeriod(models.Model):
    DAY_CHOICES = [
        ('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'), ('Friday', 'Friday'),
    ]

    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    subject = models.CharField(max_length=100)
    # SY-28: optional link to the canonical MANEB subject/paper so a
    # timetable stays aligned even as `subject` free text drifts.
    syllabus_subject = models.ForeignKey(
        'syllabus.Subject', on_delete=models.SET_NULL, null=True, blank=True, related_name='timetable_periods',
    )
    syllabus_paper = models.ForeignKey(
        'syllabus.Paper', on_delete=models.SET_NULL, null=True, blank=True, related_name='timetable_periods',
    )
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True)
    class_name = models.CharField(max_length=10)
    stream = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B')])

    class Meta:
        ordering = ['day', 'start_time']

    def __str__(self):
        return f'{self.day} {self.start_time}-{self.end_time}: {self.subject} ({self.class_name}{self.stream})'

    def clean(self):
        # TC-13: a teacher cannot be scheduled for two classes at once.
        if not self.teacher_id or not self.day or not self.start_time or not self.end_time:
            return
        overlapping = TimetablePeriod.objects.filter(
            teacher_id=self.teacher_id, day=self.day,
            start_time__lt=self.end_time, end_time__gt=self.start_time,
        ).exclude(pk=self.pk)
        if overlapping.exists():
            clash = overlapping.first()
            raise ValidationError(
                f'{self.teacher} is already teaching {clash.subject} for '
                f'{clash.class_name}{clash.stream} on {self.day} at that time.'
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def time_range(self):
        return f'{self.start_time.strftime("%H:%M")} - {self.end_time.strftime("%H:%M")}'

    @property
    def class_display(self):
        return f'{self.class_name}{self.stream}'
