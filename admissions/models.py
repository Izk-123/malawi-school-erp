import datetime
import secrets

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords

from accounts.models import malawi_phone_validator
from students.models import Student


def generate_applicant_code():
    """AD-43-style: a short human-readable applicant code, e.g. APP-7KP3QX.
    Excludes confusable characters (0/O, 1/I/L)."""
    alphabet = '23456789ABCDEFGHJKMNPQRSTUVWXYZ'
    return 'APP-' + ''.join(secrets.choice(alphabet) for _ in range(6))


class Enquiry(models.Model):
    """AD-01..AD-07: front-office lead capture. Not a Student, not yet an
    Applicant — just a lead that gets followed up."""

    class Source(models.TextChoices):
        WALK_IN = 'walk_in', 'Walk-in'
        PHONE = 'phone', 'Phone call'
        WEBSITE = 'website', 'Website form'
        WHATSAPP = 'whatsapp', 'WhatsApp'
        FACEBOOK = 'facebook', 'Facebook'
        RADIO = 'radio', 'Radio'
        REFERRAL = 'referral', 'Referral from existing parent'
        CHURCH = 'church', 'Church'
        WORD_OF_MOUTH = 'word_of_mouth', 'Word of mouth'
        OTHER = 'other', 'Other'

    class Status(models.TextChoices):
        NEW = 'new', 'New'
        FOLLOWED_UP = 'followed_up', 'Followed up'
        CONVERTED = 'converted', 'Converted to applicant'
        LOST = 'lost', 'Lost'

    source = models.CharField(max_length=20, choices=Source.choices)
    enquiry_date = models.DateField(default=datetime.date.today, db_index=True)
    parent_name = models.CharField(max_length=150)
    guardian_phone = models.CharField(
        max_length=20, validators=[malawi_phone_validator], db_index=True,
    )
    guardian_email = models.EmailField(blank=True)
    student_name = models.CharField(max_length=150)
    current_class = models.CharField(
        max_length=30, blank=True,
        help_text="e.g. 'PSLCE candidate', 'Form 2'.",
    )
    applying_for = models.CharField(max_length=10, help_text='Form 1, 2, 3, or 4.')
    boarding_preference = models.CharField(
        max_length=10,
        choices=[('day', 'Day scholar'), ('boarder', 'Boarder')],
        default='day',
    )
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.NEW, db_index=True,
    )
    follow_up_due = models.DateField(null=True, blank=True)
    followed_up_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='enquiries_followed_up',
    )
    followed_up_at = models.DateTimeField(null=True, blank=True)
    converted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='enquiries_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['-enquiry_date', '-created_at']
        indexes = [models.Index(fields=['status']), models.Index(fields=['guardian_phone'])]

    def __str__(self):
        return f'Enquiry: {self.student_name} ({self.guardian_phone})'


class Applicant(models.Model):
    """AD-08..AD-15: a candidate who has applied. Converted to a Student
    on admission."""

    class Status(models.TextChoices):
        APPLIED = 'applied', 'Applied'
        EXAM_SCHEDULED = 'exam_scheduled', 'Exam scheduled'
        EXAM_COMPLETED = 'exam_completed', 'Exam completed'
        INTERVIEW_SCHEDULED = 'interview_scheduled', 'Interview scheduled'
        INTERVIEWED = 'interviewed', 'Interviewed'
        OFFERED = 'offered', 'Offered'
        OFFER_ACCEPTED = 'offer_accepted', 'Offer accepted'
        FEES_PAID = 'fees_paid', 'Fees paid'
        ADMITTED = 'admitted', 'Admitted'
        WAITLISTED = 'waitlisted', 'Waitlisted'
        DECLINED = 'declined', 'Declined'
        WITHDRAWN = 'withdrawn', 'Withdrawn'

    TERMINAL_STATUSES = {Status.ADMITTED, Status.DECLINED, Status.WITHDRAWN}

    class Gender(models.TextChoices):
        MALE = 'Male', 'Male'
        FEMALE = 'Female', 'Female'

    applicant_code = models.CharField(
        max_length=12, unique=True, default=generate_applicant_code, editable=False,
    )
    enquiry = models.ForeignKey(
        Enquiry, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='applicants',
    )

    # Bio
    full_name = models.CharField(max_length=150, db_index=True)
    gender = models.CharField(max_length=6, choices=Gender.choices)
    date_of_birth = models.DateField()
    national_id = models.CharField(max_length=30, blank=True)
    photo = models.ImageField(upload_to='applicant_photos/', blank=True, null=True)
    address = models.TextField(blank=True)

    # Guardian
    guardian_name = models.CharField(max_length=150)
    guardian_phone = models.CharField(
        max_length=20, validators=[malawi_phone_validator], db_index=True,
    )
    guardian_email = models.EmailField(blank=True)
    guardian_relationship = models.CharField(max_length=50, blank=True)
    guardian_national_id = models.CharField(max_length=30, blank=True)

    # Academic
    previous_school = models.CharField(max_length=200, blank=True)
    prior_academic_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text='PSLCE aggregate or equivalent (0-100).',
    )
    pslce_number = models.CharField(max_length=20, blank=True, db_index=True)

    # Preferences
    applying_for = models.CharField(max_length=10)
    boarding_preference = models.CharField(
        max_length=10,
        choices=[('day', 'Day scholar'), ('boarder', 'Boarder')],
        default='day',
    )

    # Lifecycle
    status = models.CharField(
        max_length=25, choices=Status.choices, default=Status.APPLIED, db_index=True,
    )

    # Scores (populated incrementally as stages complete)
    exam_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    interview_student_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    interview_parent_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    priority_bonus = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    composite_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, db_index=True)

    # Outcome
    offer_sent_at = models.DateTimeField(null=True, blank=True)
    offer_deadline = models.DateField(null=True, blank=True)
    offer_accepted_at = models.DateTimeField(null=True, blank=True)
    declined_reason = models.CharField(max_length=255, blank=True)
    admitted_at = models.DateTimeField(null=True, blank=True)
    admitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='applicants_admitted',
    )
    student = models.OneToOneField(
        Student, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='applicant_record',
    )
    special_consideration = models.BooleanField(
        default=False,
        help_text='AD-60: cutoff override, Head Teacher only.',
    )
    special_consideration_reason = models.CharField(max_length=255, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='applicants_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['-composite_score', '-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['composite_score']),
            models.Index(fields=['guardian_phone']),
        ]

    def __str__(self):
        return f'{self.applicant_code}: {self.full_name} ({self.get_status_display()})'

    @property
    def is_terminal(self):
        return self.status in self.TERMINAL_STATUSES


class DocumentAttachment(models.Model):
    """AD-15: document uploads with verification flag."""

    class DocType(models.TextChoices):
        PSLCE = 'pslce', 'PSLCE certificate/results'
        BIRTH_CERT = 'birth_cert', 'Birth certificate or affidavit'
        TRANSFER_LETTER = 'transfer_letter', 'Transfer letter'
        REPORT_CARD = 'report_card', 'Last report card'
        GUARDIAN_ID = 'guardian_id', 'Guardian national ID'
        PHOTO = 'photo', 'Passport photos'
        MEDICAL = 'medical', 'Medical/allergy record'
        OTHER = 'other', 'Other'

    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DocType.choices)
    file = models.FileField(upload_to='admission_docs/%Y/%m/')
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='documents_verified',
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'{self.get_document_type_display()} — {self.applicant.full_name}'


class ApplicantPriority(models.Model):
    """AD-11: a priority flag attached to an applicant. `bonus_points` is
    copied from `constants.PRIORITY_BONUSES` at creation time so the
    score stays stable even if the constant changes later."""

    class FlagType(models.TextChoices):
        SIBLING = 'sibling', 'Sibling of current student'
        STAFF_CHILD = 'staff_child', 'Child of staff member'
        ALUMNI_CHILD = 'alumni_child', 'Child of alumni'
        BOARD_DIRECTIVE = 'board_directive', 'Board directive'
        SPECIAL_CONSIDERATION = 'special_consideration', 'Special consideration (cutoff override)'

    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='priority_flags')
    flag_type = models.CharField(max_length=25, choices=FlagType.choices)
    bonus_points = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    reason = models.CharField(max_length=255, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('applicant', 'flag_type')
        ordering = ['-bonus_points']

    def __str__(self):
        return f'{self.get_flag_type_display()} (+{self.bonus_points}) — {self.applicant.full_name}'


class EntranceExam(models.Model):
    """AD-16..AD-22: exam session with capacity and cutoff."""

    name = models.CharField(max_length=150)
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    venue = models.CharField(max_length=150)
    capacity = models.PositiveIntegerField(default=100)
    cutoff_score = models.DecimalField(max_digits=5, decimal_places=2, default=40)
    is_published = models.BooleanField(
        default=False, help_text='Marks final; downstream offers allowed.',
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='exam_sessions_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['-exam_date']

    def __str__(self):
        return f'{self.name} ({self.exam_date})'

    @property
    def registered_count(self):
        return self.assignments.count()

    @property
    def seats_available(self):
        return max(0, self.capacity - self.registered_count)


class ExamAssignment(models.Model):
    """AD-17/18/21: an applicant's seat at a specific session."""

    class Attendance(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ATTENDED = 'attended', 'Attended'
        ABSENT = 'absent', 'Absent'

    session = models.ForeignKey(EntranceExam, on_delete=models.CASCADE, related_name='assignments')
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='exam_assignments')
    seat_number = models.CharField(max_length=10)
    attended = models.CharField(max_length=10, choices=Attendance.choices, default=Attendance.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('session', 'applicant'), ('session', 'seat_number')]

    def __str__(self):
        return f'{self.applicant.full_name} @ {self.session.name} seat {self.seat_number}'


class ExamMark(models.Model):
    """AD-19: per-subject mark per assignment."""

    class Subject(models.TextChoices):
        ENGLISH = 'english', 'English'
        MATHEMATICS = 'mathematics', 'Mathematics'
        GENERAL_KNOWLEDGE = 'general_knowledge', 'General Knowledge'
        CHICHEWA = 'chichewa', 'Chichewa'

    assignment = models.ForeignKey(ExamAssignment, on_delete=models.CASCADE, related_name='marks')
    subject = models.CharField(max_length=20, choices=Subject.choices)
    score = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        unique_together = ('assignment', 'subject')

    def __str__(self):
        return f'{self.assignment.applicant.full_name} {self.get_subject_display()}: {self.score}'


class Interview(models.Model):
    """AD-23..AD-26: interview record."""

    class Recommendation(models.TextChoices):
        STRONG_YES = 'strong_yes', 'Strong yes'
        YES = 'yes', 'Yes'
        MAYBE = 'maybe', 'Maybe'
        NO = 'no', 'No'

    applicant = models.OneToOneField(Applicant, on_delete=models.CASCADE, related_name='interview')
    scheduled_for = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=150, blank=True)
    interviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='interviews_conducted',
    )
    student_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    parent_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    recommendation = models.CharField(max_length=15, choices=Recommendation.choices, blank=True)
    conducted_at = models.DateTimeField(null=True, blank=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['-scheduled_for']

    def __str__(self):
        return f'Interview — {self.applicant.full_name}'


class Offer(models.Model):
    """AD-27..AD-34: offer lifecycle with auto-expiry."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        DECLINED = 'declined', 'Declined'
        EXPIRED = 'expired', 'Expired'

    applicant = models.OneToOneField(Applicant, on_delete=models.CASCADE, related_name='offer')
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='offers_issued',
    )
    issued_at = models.DateTimeField(auto_now_add=True)
    response_deadline = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    accepted_at = models.DateTimeField(null=True, blank=True)
    declined_at = models.DateTimeField(null=True, blank=True)
    decline_reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['-issued_at']

    def __str__(self):
        return f'Offer — {self.applicant.full_name} ({self.status})'

    def is_expired(self):
        return self.status == self.Status.PENDING and self.response_deadline < timezone.now().date()

    def accept(self):
        if self.status != self.Status.PENDING:
            raise ValidationError('Only pending offers can be accepted.')
        self.status = self.Status.ACCEPTED
        self.accepted_at = timezone.now()
        self.save(update_fields=['status', 'accepted_at'])
        self.applicant.status = Applicant.Status.OFFER_ACCEPTED
        self.applicant.offer_accepted_at = timezone.now()
        self.applicant.save(update_fields=['status', 'offer_accepted_at'])

    def decline(self, reason=''):
        if self.status != self.Status.PENDING:
            raise ValidationError('Only pending offers can be declined.')
        self.status = self.Status.DECLINED
        self.declined_at = timezone.now()
        self.decline_reason = reason
        self.save(update_fields=['status', 'declined_at', 'decline_reason'])
        self.applicant.status = Applicant.Status.DECLINED
        self.applicant.declined_reason = reason
        self.applicant.save(update_fields=['status', 'declined_reason'])

    def expire(self):
        if self.status != self.Status.PENDING:
            return False
        self.status = self.Status.EXPIRED
        self.save(update_fields=['status'])
        self.applicant.status = Applicant.Status.DECLINED
        self.applicant.declined_reason = 'Offer deadline passed'
        self.applicant.save(update_fields=['status', 'declined_reason'])
        return True


class WaitlistEntry(models.Model):
    """AD-35..AD-39: FIFO position per class/stream."""

    applicant = models.OneToOneField(Applicant, on_delete=models.CASCADE, related_name='waitlist_entry')
    class_name = models.CharField(max_length=10)
    stream = models.CharField(max_length=1)
    position = models.PositiveIntegerField()
    added_at = models.DateTimeField(auto_now_add=True)
    promoted_at = models.DateTimeField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = [('class_name', 'stream', 'position')]
        ordering = ['class_name', 'stream', 'position']

    def __str__(self):
        return f'Waitlist #{self.position} — {self.applicant.full_name} ({self.class_name}{self.stream})'

    @classmethod
    def next_position(cls, class_name, stream):
        last = cls.objects.filter(class_name=class_name, stream=stream).order_by('-position').first()
        return (last.position + 1) if last else 1