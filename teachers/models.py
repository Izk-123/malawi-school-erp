import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from simple_history.models import HistoricalRecords


class Subject(models.Model):
    """TC-06/07: subjects a teacher may be qualified to teach."""
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Teacher(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        ON_LEAVE = 'on_leave', 'On Leave'
        INACTIVE = 'inactive', 'Inactive'
        RETIRED = 'retired', 'Retired'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='teacher_profile',
    )
    teacher_id = models.CharField(max_length=15, unique=True, blank=True, db_index=True)
    full_name = models.CharField(max_length=150, db_index=True)
    photo = models.ImageField(upload_to='teacher_photos/', blank=True, null=True)
    gender = models.CharField(max_length=6, choices=[('Male', 'Male'), ('Female', 'Female')], blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    # TC-08: primary subject/specialization for display; TC-06/07: full set below.
    subject = models.CharField(max_length=100, help_text='Primary subject / specialization')
    subjects = models.ManyToManyField(Subject, blank=True, related_name='teachers')
    # SY-26: subjects/papers this teacher teaches per the MANEB syllabus,
    # kept separate from the lightweight `subjects` field above (which
    # predates the syllabus app and is just a free-form specialization list).
    syllabus_subjects = models.ManyToManyField(
        'syllabus.Subject', blank=True, related_name='teachers_assigned',
        help_text='MANEB subjects (with official codes) this teacher is qualified to teach.',
    )
    syllabus_papers = models.ManyToManyField(
        'syllabus.Paper', blank=True, related_name='teachers_assigned',
        help_text='Specific papers this teacher is qualified to teach (e.g. Physics Paper II - practical).',
    )
    qualification = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, db_index=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    hired_on = models.DateField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['full_name']
        indexes = [models.Index(fields=['status']), models.Index(fields=['subject'])]

    def __str__(self):
        return f'{self.full_name} ({self.subject})'

    # -- TC-04: auto-generate a unique teacher ID like TCH-2025-001 --------
    def _generate_teacher_id(self):
        year = self.hired_on.year if self.hired_on else datetime.date.today().year
        prefix = f'TCH-{year}-'
        last = (
            Teacher.objects.filter(teacher_id__startswith=prefix)
            .order_by('-teacher_id')
            .values_list('teacher_id', flat=True)
            .first()
        )
        next_seq = int(last.split('-')[-1]) + 1 if last else 1
        return f'{prefix}{next_seq:03d}'

    def clean(self):
        # TC-05: prevent duplicates based on name + phone number.
        if self.full_name and self.phone_number:
            duplicate = Teacher.objects.filter(
                full_name__iexact=self.full_name, phone_number=self.phone_number,
            ).exclude(pk=self.pk)
            if duplicate.exists():
                raise ValidationError('A teacher with this name and phone number already exists.')

    def save(self, *args, **kwargs):
        if not self.teacher_id:
            if not self.hired_on:
                self.hired_on = datetime.date.today()
            self.teacher_id = self._generate_teacher_id()
        super().save(*args, **kwargs)

    def classes_taught_list(self):
        return list(
            self.assignments.values_list('class_name', 'stream').distinct()
        )

    @property
    def topics_in_scope(self):
        """SY-26: all syllabus topics across the subjects this teacher teaches."""
        from syllabus.models import SyllabusTopic
        return SyllabusTopic.objects.filter(subject__in=self.syllabus_subjects.all(), is_active=True)


class TeacherCertification(models.Model):
    """TC-10: optional certifications / professional development records."""
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='certifications')
    title = models.CharField(max_length=150)
    issuer = models.CharField(max_length=150, blank=True)
    date_obtained = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-date_obtained']

    def __str__(self):
        return f'{self.title} - {self.teacher.full_name}'


class ClassAssignment(models.Model):
    """A teacher assigned to teach a subject to a specific class/stream."""
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='assignments')
    class_name = models.CharField(max_length=10)
    stream = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B')])
    subject = models.CharField(max_length=100)

    class Meta:
        unique_together = ('teacher', 'class_name', 'stream', 'subject')

    def __str__(self):
        return f'{self.teacher.full_name} -> {self.class_name}{self.stream} ({self.subject})'

    @property
    def class_display(self):
        return f'{self.class_name}{self.stream}'
