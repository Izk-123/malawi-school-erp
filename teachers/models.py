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
    """A teacher record.

    Fields are grouped:
      * Identity / contact
      * Legacy free-text specialisation  (``subject`` / ``qualification``)
        — kept so existing templates, filters and admin lists keep working.
        Structured replacements live below and should be preferred for new
        records; the free-text fields will be retired in a later pass.
      * TCM (Teaching Council of Malawi) registration — mandatory for any
        teacher who is assigned to a class. See ``has_valid_tcm_license``.
      * Academic + professional qualifications (structured).
      * Teaching level, government grade, employment type.
    """

    # ------------------------------------------------------------------
    # Enums
    # ------------------------------------------------------------------
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        ON_LEAVE = 'on_leave', 'On Leave'
        INACTIVE = 'inactive', 'Inactive'
        RETIRED = 'retired', 'Retired'

    class TCMStatus(models.TextChoices):
        REGISTERED = 'registered', 'Registered'
        PROVISIONAL = 'provisional', 'Provisional'
        SUSPENDED = 'suspended', 'Suspended'
        EXPIRED = 'expired', 'Expired'
        NOT_REGISTERED = 'not_registered', 'Not registered'

    class AcademicQualification(models.TextChoices):
        MSCE = 'msce', 'MSCE'
        DIPLOMA = 'diploma', 'Diploma'
        DEGREE = 'degree', "Bachelor's Degree"
        MASTERS = 'masters', "Master's Degree"
        PHD = 'phd', 'PhD'

    class ProfessionalQualification(models.TextChoices):
        TEACHER_CERT = 'teacher_cert', "Teacher's Certificate (2-year TTC)"
        DIPLOMA_ED = 'diploma_ed', 'Diploma in Education'
        BED = 'bed', 'Bachelor of Education (B.Ed.)'
        DEGREE_UCE = 'degree_uce', 'Degree + University Certificate of Education (UCE)'
        PGDE = 'pgde', 'Postgraduate Diploma in Education'
        NONE = 'none', 'None — unqualified'

    class TeachingLevel(models.TextChoices):
        PRIMARY = 'primary', 'Primary'
        SECONDARY = 'secondary', 'Secondary'
        BOTH = 'both', 'Both'

    class GovernmentGrade(models.TextChoices):
        # Primary ladder (promotional; PT2/PT1 also carry headship)
        PT4 = 'PT4', 'PT4 (entry)'
        PT3 = 'PT3', 'PT3'
        PT2 = 'PT2', 'PT2 (headship)'
        PT1 = 'PT1', 'PT1 (headship)'
        # Secondary ladder
        TI = 'TI', 'TI (entry)'
        TJ = 'TJ', 'TJ'
        # Private / church schools: leave blank — do not use a sentinel value.

    class EmploymentType(models.TextChoices):
        GOVERNMENT = 'government', 'Government (TSC)'
        PRIVATE = 'private', 'Private (school-employed)'
        CHURCH = 'church', 'Church / mission'
        VOLUNTEER = 'volunteer', 'Volunteer'

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='teacher_profile',
    )
    teacher_id = models.CharField(max_length=15, unique=True, blank=True, db_index=True)
    full_name = models.CharField(max_length=150, db_index=True)
    photo = models.ImageField(upload_to='teacher_photos/', blank=True, null=True)
    gender = models.CharField(max_length=6, choices=[('Male', 'Male'), ('Female', 'Female')], blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    # National registration card / ID. Nullable so legacy rows migrate cleanly;
    # uniqueness is still enforced for any non-null value.
    national_id = models.CharField(max_length=20, unique=True, null=True, blank=True)

    # ------------------------------------------------------------------
    # Contact
    # ------------------------------------------------------------------
    phone_number = models.CharField(max_length=20, db_index=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    # ------------------------------------------------------------------
    # Legacy free-text specialisation  (kept so nothing breaks)
    # ------------------------------------------------------------------
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
    qualification = models.CharField(max_length=150)  # legacy free text

    # ------------------------------------------------------------------
    # TCM registration (Teaching Council of Malawi)
    # ------------------------------------------------------------------
    tcm_registration_number = models.CharField(
        max_length=30, unique=True, null=True, blank=True,
        help_text='Teaching Council of Malawi registration number.',
    )
    tcm_license_expiry = models.DateField(
        null=True, blank=True, db_index=True,
        help_text='License must be renewed — the system warns 60/30/7 days before expiry.',
    )
    tcm_status = models.CharField(
        max_length=20, choices=TCMStatus.choices, default=TCMStatus.NOT_REGISTERED,
        db_index=True,
        help_text='Registered/Provisional are the only statuses that permit class assignment.',
    )

    # ------------------------------------------------------------------
    # Academic qualifications (structured)
    # ------------------------------------------------------------------
    highest_academic_qualification = models.CharField(
        max_length=30, choices=AcademicQualification.choices, blank=True,
    )
    academic_institution = models.CharField(max_length=200, blank=True)

    # ------------------------------------------------------------------
    # Professional qualifications (structured)
    # ------------------------------------------------------------------
    professional_qualification = models.CharField(
        max_length=50, choices=ProfessionalQualification.choices, blank=True,
    )
    professional_institution = models.CharField(
        max_length=200, blank=True,
        help_text='e.g. Nalikule TTC, Domasi College, Chancellor College, Mzuzu University.',
    )
    year_qualified = models.PositiveSmallIntegerField(null=True, blank=True)

    # ------------------------------------------------------------------
    # Teaching level and (public school) grade
    # ------------------------------------------------------------------
    teaching_level = models.CharField(
        max_length=20, choices=TeachingLevel.choices, default=TeachingLevel.SECONDARY,
    )
    government_grade = models.CharField(
        max_length=10, choices=GovernmentGrade.choices, blank=True,
        help_text='Leave blank for private / church / volunteer posts.',
    )

    # ------------------------------------------------------------------
    # Employment
    # ------------------------------------------------------------------
    employment_type = models.CharField(
        max_length=20, choices=EmploymentType.choices, blank=True,
    )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    hired_on = models.DateField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['full_name']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['subject']),
            models.Index(fields=['tcm_status']),
            models.Index(fields=['tcm_license_expiry']),
        ]

    def __str__(self):
        return f'{self.full_name} ({self.subject})'

    # ------------------------------------------------------------------
    # ID generation (TC-04)
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def clean(self):
        """Cross-field invariants for a teacher record.

        These run on every ``full_clean()`` — which includes the admin's
        auto-generated ModelForm and any service-layer call that goes
        through ``full_clean()``. The form layer deliberately does not
        re-implement them; see ``teachers/forms.py`` for why.
        """
        super().clean()

        # TC-05: prevent duplicates based on name + phone number.
        if self.full_name and self.phone_number:
            duplicate = Teacher.objects.filter(
                full_name__iexact=self.full_name, phone_number=self.phone_number,
            ).exclude(pk=self.pk)
            if duplicate.exists():
                raise ValidationError('A teacher with this name and phone number already exists.')

        # A Registered/Provisional status with no number is a contradictory
        # record — refuse it rather than let it silently pass the
        # has_valid_tcm_license check later.
        if (
            self.tcm_status in (self.TCMStatus.REGISTERED, self.TCMStatus.PROVISIONAL)
            and not self.tcm_registration_number
        ):
            raise ValidationError({
                'tcm_registration_number': (
                    'A TCM registration number is required when the status is '
                    'Registered or Provisional.'
                ),
            })

        # Public-service grade must match teaching level. PT4–PT1 belong to
        # primary posts, TI/TJ to secondary — a mismatch is a data-entry
        # error, not a policy choice.
        if self.government_grade:
            primary_grades = {
                self.GovernmentGrade.PT4, self.GovernmentGrade.PT3,
                self.GovernmentGrade.PT2, self.GovernmentGrade.PT1,
            }
            secondary_grades = {
                self.GovernmentGrade.TI, self.GovernmentGrade.TJ,
            }

            if (
                self.teaching_level == self.TeachingLevel.PRIMARY
                and self.government_grade in secondary_grades
            ):
                raise ValidationError({
                    'government_grade': (
                        f'{self.government_grade} is a secondary-service grade. '
                        'A primary teacher should be on the PT4/PT3/PT2/PT1 ladder.'
                    ),
                })

            if (
                self.teaching_level == self.TeachingLevel.SECONDARY
                and self.government_grade in primary_grades
            ):
                raise ValidationError({
                    'government_grade': (
                        f'{self.government_grade} is a primary-service grade. '
                        'A secondary teacher should be on the TI/TJ ladder.'
                    ),
                })

            # Government grade only exists on the public-service ladder.
            if (
                self.employment_type
                and self.employment_type != self.EmploymentType.GOVERNMENT
            ):
                raise ValidationError({
                    'government_grade': (
                        'Government grade applies to government (TSC) posts only. '
                        'Leave it blank for private, church and volunteer roles.'
                    ),
                })

    def save(self, *args, **kwargs):
        if not self.teacher_id:
            if not self.hired_on:
                self.hired_on = datetime.date.today()
            self.teacher_id = self._generate_teacher_id()
        super().save(*args, **kwargs)

    # ------------------------------------------------------------------
    # Convenience queries / properties
    # ------------------------------------------------------------------
    def classes_taught_list(self):
        return list(
            self.assignments.values_list('class_name', 'stream').distinct()
        )

    @property
    def topics_in_scope(self):
        """SY-26: all syllabus topics across the subjects this teacher teaches."""
        from syllabus.models import SyllabusTopic
        return SyllabusTopic.objects.filter(subject__in=self.syllabus_subjects.all(), is_active=True)

    @property
    def tcm_days_until_expiry(self):
        """Days from today until ``tcm_license_expiry``. ``None`` if unset."""
        if not self.tcm_license_expiry:
            return None
        return (self.tcm_license_expiry - datetime.date.today()).days

    @property
    def has_valid_tcm_license(self):
        """True iff this teacher may legally be assigned to a class.

        Registered/Provisional are the only TCM statuses that permit
        assignment; a registration number must be on file and the license
        must not be in the past. Enforcement of this property belongs in
        the assignment service layer, not here — the model just answers
        the question.
        """
        if self.tcm_status not in (self.TCMStatus.REGISTERED, self.TCMStatus.PROVISIONAL):
            return False
        if not self.tcm_registration_number:
            return False
        if self.tcm_license_expiry and self.tcm_license_expiry < datetime.date.today():
            return False
        return True

    @property
    def is_unqualified(self):
        """True when the teacher has no professional teaching qualification.

        Used to surface the 'private school hiring unqualified staff' flag
        the ISAMA policy asks the ERP to warn about.
        """
        return (
            not self.professional_qualification
            or self.professional_qualification == self.ProfessionalQualification.NONE
        )


class TeacherQualification(models.Model):
    """A single formal qualification held by a teacher.

    Kept deliberately separate from :class:`TeacherCertification`:

      * ``TeacherQualification`` — formal academic / professional
        credentials (MSCE, Diploma in Education, B.Ed., PGDE…) with a
        verification flag and a certificate scan.
      * ``TeacherCertification`` — short courses, workshops and CPD
        records (unchanged; free-form ``title``).

    A teacher typically has several rows here, all attached to the same
    ``Teacher``.
    """

    class QualificationType(models.TextChoices):
        # Academic
        MSCE = 'msce', 'MSCE'
        DIPLOMA = 'diploma', 'Diploma'
        DEGREE = 'degree', "Bachelor's Degree"
        MASTERS = 'masters', "Master's Degree"
        PHD = 'phd', 'PhD'
        # Professional
        TEACHER_CERT = 'teacher_cert', "Teacher's Certificate (2-year TTC)"
        DIPLOMA_ED = 'diploma_ed', 'Diploma in Education'
        BED = 'bed', 'Bachelor of Education (B.Ed.)'
        DEGREE_UCE = 'degree_uce', 'Degree + University Certificate of Education (UCE)'
        PGDE = 'pgde', 'Postgraduate Diploma in Education'
        # Fallback — used by the eventual data migration from
        # TeacherCertification, and for any future qualification type.
        OTHER = 'other', 'Other'

    teacher = models.ForeignKey(
        Teacher, on_delete=models.CASCADE, related_name='qualifications',
    )
    qualification_type = models.CharField(max_length=30, choices=QualificationType.choices)
    institution = models.CharField(max_length=200)
    year_obtained = models.PositiveSmallIntegerField()
    certificate = models.FileField(upload_to='teacher_certs/', blank=True)
    verified = models.BooleanField(
        default=False,
        help_text='Set once an administrator has checked the certificate scan.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-year_obtained']
        indexes = [
            models.Index(fields=['teacher', 'qualification_type']),
        ]

    def __str__(self):
        return f'{self.get_qualification_type_display()} ({self.year_obtained}) — {self.teacher.full_name}'


class TCMLicenseRenewal(models.Model):
    """Audit trail of every TCM license renewal for a teacher.

    Each row corresponds to one receipt: how much was paid, when the new
    license expires, and (optionally) a scan of the certificate. The
    teacher's ``tcm_license_expiry`` is expected to track the maximum
    ``expires_at`` across these rows — that roll-up happens in the
    service layer, not in a signal, so it stays testable.
    """

    teacher = models.ForeignKey(
        Teacher, on_delete=models.CASCADE, related_name='license_renewals',
    )
    renewed_at = models.DateField()
    expires_at = models.DateField()
    receipt_number = models.CharField(max_length=50)
    renewal_fee_paid = models.DecimalField(max_digits=10, decimal_places=2)
    document = models.FileField(upload_to='tcm_licenses/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-renewed_at']
        indexes = [
            models.Index(fields=['teacher', 'expires_at']),
        ]

    def __str__(self):
        return f'{self.teacher.full_name} — renewed {self.renewed_at}, expires {self.expires_at}'


class GradePromotion(models.Model):
    """A single step on the public-school grade ladder (PT4 → PT3 → PT2 → PT1,
    or TI → TJ).

    Kept as a first-class record so a promotion is auditable: who approved
    it, when, and why. The teacher's current ``government_grade`` is a
    denormalised cache of the latest row.
    """

    teacher = models.ForeignKey(
        Teacher, on_delete=models.CASCADE, related_name='grade_promotions',
    )
    from_grade = models.CharField(max_length=10)  # PT4 / PT3 / PT2 / PT1 / TI / TJ
    to_grade = models.CharField(max_length=10)
    promoted_at = models.DateField()
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='grade_promotions_approved',
    )
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-promoted_at']
        indexes = [
            models.Index(fields=['teacher', 'promoted_at']),
        ]

    def __str__(self):
        return f'{self.teacher.full_name}: {self.from_grade} → {self.to_grade} ({self.promoted_at})'


class TeacherCertification(models.Model):
    """TC-10: optional certifications / professional development records.

    Unchanged from before — kept separate from :class:`TeacherQualification`
    so CPD/workshop records don't get tangled up with formal credentials.
    """
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