import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from simple_history.models import HistoricalRecords

from accounts.models import malawi_phone_validator


class Student(models.Model):
    class Gender(models.TextChoices):
        MALE = 'Male', 'Male'
        FEMALE = 'Female', 'Female'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        PENDING = 'pending', 'Pending'
        SUSPENDED = 'suspended', 'Suspended'
        GRADUATED = 'graduated', 'Graduated'
        TRANSFERRED = 'transferred', 'Transferred'
        INACTIVE = 'inactive', 'Inactive'

    ARCHIVED_STATUSES = {Status.GRADUATED, Status.TRANSFERRED, Status.INACTIVE}

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='student_profile',
    )
    student_id = models.CharField(max_length=15, unique=True, blank=True, db_index=True)
    full_name = models.CharField(max_length=150, db_index=True)
    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    gender = models.CharField(max_length=6, choices=Gender.choices)
    date_of_birth = models.DateField()
    guardian_name = models.CharField(max_length=150)
    guardian_phone = models.CharField(max_length=20, validators=[malawi_phone_validator], db_index=True, blank=True)
    guardians = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='children', blank=True,
        limit_choices_to={'role': 'parent'},
        help_text='Linked parent accounts (for the Parent portal).',
    )
    address = models.TextField(blank=True)
    class_name = models.CharField(max_length=10, help_text="e.g. 'Form 3'", db_index=True)
    stream = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B')], default='A')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    fees_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fees_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    average_grade = models.CharField(max_length=3, blank=True, default='N/A')
    enrolled_on = models.DateField(auto_now_add=True)
    # SY-24/25: which MSCE session this student is preparing for, and the
    # syllabus subjects they're actually registered for this term.
    exam_session = models.ForeignKey(
        'syllabus.ExamSession', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='students',
    )
    enrolled_subjects = models.ManyToManyField(
        'syllabus.Subject', blank=True, related_name='enrolled_students',
        help_text='MANEB subjects this student is registered for this term.',
    )
    history = HistoricalRecords()

    class Meta:
        ordering = ['class_name', 'stream', 'full_name']
        indexes = [
            models.Index(fields=['class_name', 'stream']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.full_name} ({self.student_id})'

    # -- ST-05: auto-generate a unique student ID like STU-2025-001 --------
    def _generate_student_id(self):
        year = self.enrolled_on.year if self.enrolled_on else datetime.date.today().year
        prefix = f'STU-{year}-'
        last = (
            Student.objects.filter(student_id__startswith=prefix)
            .order_by('-student_id')
            .values_list('student_id', flat=True)
            .first()
        )
        next_seq = int(last.split('-')[-1]) + 1 if last else 1
        return f'{prefix}{next_seq:03d}'

    def clean(self):
        # ST-06: prevent duplicates based on name + DOB + guardian phone.
        if self.full_name and self.date_of_birth and self.guardian_phone:
            duplicate = Student.objects.filter(
                full_name__iexact=self.full_name,
                date_of_birth=self.date_of_birth,
                guardian_phone=self.guardian_phone,
            ).exclude(pk=self.pk)
            if duplicate.exists():
                raise ValidationError(
                    'A student with this name, date of birth, and guardian phone already exists.'
                )

    def save(self, *args, **kwargs):
        if not self.student_id:
            # enrolled_on isn't set until first save (auto_now_add); use today for new records.
            if not self.enrolled_on:
                self.enrolled_on = datetime.date.today()
            self.student_id = self._generate_student_id()
        super().save(*args, **kwargs)

    @property
    def class_display(self):
        return f'{self.class_name} {self.stream}'

    @property
    def is_archived(self):
        return self.status in self.ARCHIVED_STATUSES

    @property
    def balance(self):
        return self.fees_total - self.fees_paid

    @property
    def fees_percentage(self):
        if not self.fees_total:
            return 0
        return round((self.fees_paid / self.fees_total) * 100)

    @property
    def fee_status(self):
        pct = self.fees_percentage
        if pct >= 80:
            return 'paid'
        if pct >= 30:
            return 'partial'
        return 'due'

    def recompute_attendance(self):
        records = self.attendance_records.all()
        total = records.count()
        if not total:
            return
        present = records.filter(status__in=['present', 'late']).count()
        self.attendance_percentage = round((present / total) * 100, 2)
        self.save(update_fields=['attendance_percentage'])

    def recompute_average_grade(self):
        from grades.models import GradeRecord
        records = GradeRecord.objects.filter(student=self)
        if not records:
            return
        avg_score = sum(r.score for r in records) / records.count()
        self.average_grade = GradeRecord.score_to_letter(avg_score)
        self.save(update_fields=['average_grade'])


class GuardianContact(models.Model):
    """ST-07/08/09/10: a student may have several guardians/contacts;
    one can be marked primary and optionally linked to a Parent account."""

    class Relationship(models.TextChoices):
        MOTHER = 'mother', 'Mother'
        FATHER = 'father', 'Father'
        GRANDPARENT = 'grandparent', 'Grandparent'
        SIBLING = 'sibling', 'Sibling'
        UNCLE_AUNT = 'uncle_aunt', 'Uncle/Aunt'
        GUARDIAN = 'guardian', 'Legal Guardian'
        OTHER = 'other', 'Other'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='guardian_contacts')
    name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, validators=[malawi_phone_validator])
    relationship = models.CharField(max_length=20, choices=Relationship.choices, default=Relationship.GUARDIAN)
    is_primary = models.BooleanField(default=False)
    linked_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        limit_choices_to={'role': 'parent'}, related_name='guardian_contact_entries',
    )

    class Meta:
        ordering = ['-is_primary', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_relationship_display()}) - {self.student.full_name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Keep GuardianContact.linked_user in sync with Student.guardians M2M
        # so the Parent portal (which queries `guardians`) sees this contact.
        if self.linked_user:
            self.student.guardians.add(self.linked_user)
        if self.is_primary:
            GuardianContact.objects.filter(student=self.student).exclude(pk=self.pk).update(is_primary=False)
