"""Admissions service layer — every cross-model write goes through here,
never from a view (NFR §5 Maintainability).

Current integration points (before the `parents` and `academics` apps are
extracted — see the app-boundaries doc):

  * Parent / guardian info lives on `students.Student` (guardian_name,
    guardian_phone, guardians M2M) and `students.GuardianContact`. There
    is no separate `parents` app yet; `admit_applicant` writes the
    GuardianContact row directly, and the invitation-claim flow links
    the eventual User into `Student.guardians`.

  * Class and stream are `CharField` values on `students.Student`
    (class_name, stream), not FK'd to an `academics.Stream` model. The
    capacity check falls back to `DEFAULT_STREAM_CAPACITY` until that
    model exists — see `_stream_capacity` below for the SEAM.

  * Fee totals come from `fees.FeeStructure` (unique on
    class_name + stream + term). We take the most recent one for the
    class+stream, since the Student model has no "current term" field.

  * Boarding has no home on Student yet, so `boarding_status`, `hostel`,
    and `bed_number` are logged rather than persisted. SEAM_BOARDING
    marks the exact spot that will change.
"""
import datetime
import logging
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Avg
from django.utils import timezone

from accounts.services import issue_admission_invitations
from fees.models import FeeStructure
from students.models import Student
from .constants import (
    COMPOSITE_WEIGHTS, DEFAULT_OFFER_DEADLINE_DAYS, DEFAULT_STREAM_CAPACITY,
    PRIORITY_BONUSES,
)
from .models import (
    Applicant, ApplicantPriority, Enquiry, ExamAssignment, ExamMark,
    Offer, WaitlistEntry,
)

logger = logging.getLogger(__name__)


# ── Relationship mapping (applicant free-text → GuardianContact choice) ─
_RELATIONSHIP_MAP = {
    'mother': 'mother',
    'father': 'father',
    'mum': 'mother',
    'dad': 'father',
    'grandparent': 'grandparent',
    'grandmother': 'grandparent',
    'grandfather': 'grandparent',
    'sibling': 'sibling',
    'brother': 'sibling',
    'sister': 'sibling',
    'uncle': 'uncle_aunt',
    'aunt': 'uncle_aunt',
    'guardian': 'guardian',
    'legal guardian': 'guardian',
    'other': 'other',
}


def _map_relationship(raw):
    """Best-effort mapping of a free-text applicant.guardian_relationship
    into a `GuardianContact.Relationship` value. Defaults to 'guardian'."""
    if not raw:
        return 'guardian'
    return _RELATIONSHIP_MAP.get(raw.strip().lower(), 'guardian')


# ── Enquiry → Applicant ─────────────────────────────────────────────
@transaction.atomic
def convert_enquiry_to_applicant(enquiry, *, created_by, **overrides):
    """AD-06: convert an enquiry to an applicant with prefilled data."""
    if enquiry.status == Enquiry.Status.CONVERTED:
        raise ValidationError('This enquiry has already been converted.')

    defaults = dict(
        enquiry=enquiry,
        full_name=enquiry.student_name,
        guardian_name=enquiry.parent_name,
        guardian_phone=enquiry.guardian_phone,
        guardian_email=enquiry.guardian_email,
        applying_for=enquiry.applying_for,
        boarding_preference=enquiry.boarding_preference,
        gender=overrides.pop('gender', Applicant.Gender.MALE),
        date_of_birth=overrides.pop('date_of_birth', datetime.date(2010, 1, 1)),
        created_by=created_by,
    )
    defaults.update(overrides)

    applicant = Applicant.objects.create(**defaults)
    _auto_detect_priorities(applicant)

    enquiry.status = Enquiry.Status.CONVERTED
    enquiry.converted_at = timezone.now()
    enquiry.save(update_fields=['status', 'converted_at'])
    return applicant


def _auto_detect_priorities(applicant):
    """AD-11: auto-flag sibling / staff child by guardian phone.

    Sibling detection: matches against `Student.guardian_phone` (the
    field the current Student model exposes) and against
    `GuardianContact.phone_number` (for families whose primary contact
    is a secondary guardian on the existing student's record).
    """
    from students.models import GuardianContact

    has_sibling = (
        Student.objects.filter(
            guardian_phone=applicant.guardian_phone,
            status=Student.Status.ACTIVE,
        ).exists()
        or GuardianContact.objects.filter(
            phone_number=applicant.guardian_phone,
            student__status=Student.Status.ACTIVE,
        ).exists()
    )
    if has_sibling:
        ApplicantPriority.objects.get_or_create(
            applicant=applicant,
            flag_type=ApplicantPriority.FlagType.SIBLING,
            defaults={
                'bonus_points': PRIORITY_BONUSES['sibling'],
                'reason': f'Sibling enrolled (guardian phone {applicant.guardian_phone})',
            },
        )

    # Staff child: matches against the staff app's phone_number field.
    try:
        from staff.models import StaffMember
        if StaffMember.objects.filter(
            phone_number=applicant.guardian_phone,
            status=StaffMember.Status.ACTIVE,
        ).exists():
            ApplicantPriority.objects.get_or_create(
                applicant=applicant,
                flag_type=ApplicantPriority.FlagType.STAFF_CHILD,
                defaults={
                    'bonus_points': PRIORITY_BONUSES['staff_child'],
                    'reason': f'Staff member with phone {applicant.guardian_phone}',
                },
            )
    except ImportError:
        pass


# ── Composite score ─────────────────────────────────────────────────
def compute_composite_score(applicant):
    """AD-12: renormalised weighted mean over present components, plus
    the sum of priority bonuses.

    Renormalised (i.e. weights divided by the sum of weights *present*)
    so an applicant who hasn't taken the interview yet isn't penalised
    for a missing 35% of the score."""
    parts = [
        (applicant.exam_score, COMPOSITE_WEIGHTS['exam']),
        (applicant.interview_student_score, COMPOSITE_WEIGHTS['interview_student']),
        (applicant.interview_parent_score, COMPOSITE_WEIGHTS['interview_parent']),
        (applicant.prior_academic_score, COMPOSITE_WEIGHTS['prior_academic']),
    ]
    total_weight = sum(w for v, w in parts if v is not None)
    if total_weight == 0:
        return None
    weighted = sum(float(v) * w for v, w in parts if v is not None) / total_weight
    bonus = float(sum((p.bonus_points for p in applicant.priority_flags.all()), Decimal('0')))
    return round(Decimal(str(weighted)) + Decimal(str(bonus)), 2)


def recompute_applicant_score(applicant):
    applicant.priority_bonus = sum(
        (p.bonus_points for p in applicant.priority_flags.all()), Decimal('0'),
    )
    applicant.composite_score = compute_composite_score(applicant)
    applicant.save(update_fields=['priority_bonus', 'composite_score'])


# ── Exam ────────────────────────────────────────────────────────────
@transaction.atomic
def assign_applicant_to_session(*, applicant, session, seat_number=None):
    """AD-17/18: assign, enforcing capacity and uniqueness."""
    if applicant.exam_assignments.filter(session=session).exists():
        raise ValidationError('This applicant is already assigned to that session.')
    if session.seats_available <= 0:
        raise ValidationError(f'Session "{session.name}" is full.')

    if not seat_number:
        used = set(session.assignments.values_list('seat_number', flat=True))
        n = 1
        while str(n) in used:
            n += 1
        seat_number = str(n)

    assignment = ExamAssignment.objects.create(
        session=session, applicant=applicant, seat_number=seat_number,
    )
    if applicant.status == Applicant.Status.APPLIED:
        applicant.status = Applicant.Status.EXAM_SCHEDULED
        applicant.save(update_fields=['status'])
    return assignment


def record_exam_mark(*, assignment, subject, score):
    """AD-19/20: upsert a mark, recompute the applicant's exam average."""
    mark, _ = ExamMark.objects.update_or_create(
        assignment=assignment, subject=subject, defaults={'score': score},
    )
    marks = ExamMark.objects.filter(
        assignment__in=assignment.applicant.exam_assignments.all(),
    )
    if marks.exists():
        avg = marks.aggregate(avg=Avg('score'))['avg']
        assignment.applicant.exam_score = round(Decimal(str(avg)), 2)
        assignment.applicant.save(update_fields=['exam_score'])
        recompute_applicant_score(assignment.applicant)
    return mark


def publish_exam_results(session):
    """AD-22: finalise marks; move attended applicants to EXAM_COMPLETED."""
    session.is_published = True
    session.save(update_fields=['is_published'])
    attended_ids = session.assignments.filter(
        attended=ExamAssignment.Attendance.ATTENDED,
    ).values_list('applicant_id', flat=True)
    Applicant.objects.filter(id__in=attended_ids).update(
        status=Applicant.Status.EXAM_COMPLETED,
    )


# ── Interview ───────────────────────────────────────────────────────
@transaction.atomic
def record_interview(*, applicant, interviewer, student_score, parent_score,
                     notes='', recommendation='', location='', conducted_at=None):
    """AD-23..AD-26: upsert interview, feed back into composite score."""
    from .models import Interview
    interview, _ = Interview.objects.update_or_create(
        applicant=applicant,
        defaults=dict(
            interviewer=interviewer,
            student_score=student_score,
            parent_score=parent_score,
            notes=notes,
            recommendation=recommendation,
            location=location,
            conducted_at=conducted_at or timezone.now(),
        ),
    )
    applicant.interview_student_score = student_score
    applicant.interview_parent_score = parent_score
    applicant.status = Applicant.Status.INTERVIEWED
    applicant.save(update_fields=[
        'interview_student_score', 'interview_parent_score', 'status',
    ])
    recompute_applicant_score(applicant)
    return interview


# ── Offer ───────────────────────────────────────────────────────────
@transaction.atomic
def issue_offer(*, applicant, issued_by, deadline_days=None, notes=''):
    """AD-27/28/31: issue offer, prevent duplicates, set deadline."""
    if applicant.status in Applicant.TERMINAL_STATUSES:
        raise ValidationError(
            f'Cannot offer — applicant is {applicant.get_status_display()}.',
        )
    if Offer.objects.filter(applicant=applicant).exclude(
        status=Offer.Status.EXPIRED,
    ).exists():
        raise ValidationError('An active offer already exists for this applicant.')

    deadline_days = deadline_days or DEFAULT_OFFER_DEADLINE_DAYS
    deadline_days = max(1, min(60, int(deadline_days)))
    deadline = timezone.now().date() + datetime.timedelta(days=deadline_days)

    offer = Offer.objects.create(
        applicant=applicant, issued_by=issued_by,
        response_deadline=deadline, notes=notes,
    )
    applicant.status = Applicant.Status.OFFERED
    applicant.offer_sent_at = timezone.now()
    applicant.offer_deadline = deadline
    applicant.save(update_fields=['status', 'offer_sent_at', 'offer_deadline'])

    # AD-29/30: async PDF + SMS.
    from .tasks import generate_offer_letter, send_offer_sms
    generate_offer_letter.delay(offer.id)
    send_offer_sms.delay(offer.id)
    return offer


def expire_stale_offers():
    """AD-33/34: called daily by Celery beat."""
    today = timezone.now().date()
    stale = Offer.objects.filter(
        status=Offer.Status.PENDING, response_deadline__lt=today,
    )
    count = 0
    for offer in stale:
        if offer.expire():
            count += 1
            logger.info(
                'Expired offer for applicant %s (deadline %s)',
                offer.applicant_id, offer.response_deadline,
            )
    return count


# ── Waitlist ────────────────────────────────────────────────────────
@transaction.atomic
def add_to_waitlist(*, applicant, class_name, stream, notes=''):
    """AD-35/38: FIFO position per class+stream; unique per applicant."""
    if WaitlistEntry.objects.filter(applicant=applicant).exists():
        raise ValidationError('Applicant is already on a waitlist.')
    position = WaitlistEntry.next_position(class_name, stream)
    entry = WaitlistEntry.objects.create(
        applicant=applicant, class_name=class_name, stream=stream,
        position=position, notes=notes,
    )
    applicant.status = Applicant.Status.WAITLISTED
    applicant.save(update_fields=['status'])
    return entry


# ── Admission (the crux) ────────────────────────────────────────────
@transaction.atomic
def admit_applicant(*, applicant, admitted_by, class_name, stream,
                    boarding_status='day', hostel='', bed_number='', reason=''):
    """AD-40..AD-48: atomic Student + guardian-contact + invitations.

    Every step is in a single transaction. If a *required* step fails,
    the whole thing rolls back — the record isn't half-created. The one
    deliberate exception is invitation delivery: an SMS-queue failure
    must not roll back an admission, so it's wrapped separately and
    logged for re-issue from the student detail page.

    SEAM_BOARDING: `boarding_status`, `hostel`, and `bed_number` are
    accepted for API stability but not persisted — `students.Student`
    has no field for them. When the boarding app lands, add the fields
    here. Until then they're logged so the information isn't silently
    dropped.
    """
    if applicant.student_id:
        raise ValidationError('This applicant has already been admitted.')
    if (applicant.status in Applicant.TERMINAL_STATUSES
            and applicant.status != Applicant.Status.OFFER_ACCEPTED):
        raise ValidationError(
            f'Cannot admit — applicant is {applicant.get_status_display()}.',
        )

    # AD-41: capacity check. SEAM_ACADEMICS below.
    capacity = _stream_capacity(class_name, stream)
    enrolled = Student.objects.filter(
        class_name=class_name, stream=stream, status=Student.Status.ACTIVE,
    ).count()
    if enrolled >= capacity:
        raise ValidationError(
            f'{class_name}{stream} is at capacity ({enrolled}/{capacity}). '
            f'Add this applicant to the waitlist instead.'
        )

    # AD-42/43/44: create the Student. Student.save() auto-generates
    # student_id (STU-YYYY-NNN) and admission_code.
    student = Student.objects.create(
        full_name=applicant.full_name,
        gender=applicant.gender,
        date_of_birth=applicant.date_of_birth,
        guardian_name=applicant.guardian_name,
        guardian_phone=applicant.guardian_phone,
        address=applicant.address or '',
        class_name=class_name,
        stream=stream,
        status=Student.Status.ACTIVE,
    )

    # SEAM_PARENTS: no separate `parents` app yet. Represent the primary
    # guardian as a GuardianContact row on the student — this is the
    # model the parent portal and the self-registration flow already
    # read, and it keeps the relationship metadata (mother/father/…)
    # that a bare Student.guardian_name would lose.
    from students.models import GuardianContact
    GuardianContact.objects.create(
        student=student,
        name=applicant.guardian_name,
        phone_number=applicant.guardian_phone,
        relationship=_map_relationship(applicant.guardian_relationship),
        is_primary=True,
    )

    # SEAM_BOARDING: not persisted — see docstring.
    if boarding_status == 'boarder':
        logger.info(
            'Applicant %s admitted as boarder (hostel=%r bed=%r) — '
            'boarding app not installed; information logged only.',
            applicant.applicant_code, hostel, bed_number,
        )

    # Fee total from FeeStructure. Student has no "current term" field,
    # so take the most recent structure for that class+stream. The
    # fees.views.RecordPaymentView continues to track actual payments.
    structure = (
        FeeStructure.objects
        .filter(class_name=class_name, stream=stream)
        .order_by('-id')
        .first()
    )
    if structure:
        student.fees_total = structure.total_amount.amount
        student.save(update_fields=['fees_total'])

    # AD-46: invitations. Wrapped separately — see docstring.
    try:
        issue_admission_invitations(
            student=student,
            issued_by=admitted_by,
            reason=(
                f'Admission from applicant {applicant.applicant_code}. {reason}'
            ).strip(),
        )
    except Exception:
        logger.exception(
            'Invitations failed for newly-admitted student %s', student.id,
        )

    # Update the applicant.
    applicant.student = student
    applicant.status = Applicant.Status.ADMITTED
    applicant.admitted_at = timezone.now()
    applicant.admitted_by = admitted_by
    applicant.save(update_fields=[
        'student', 'status', 'admitted_at', 'admitted_by',
    ])

    # Clear any waitlist entry.
    WaitlistEntry.objects.filter(applicant=applicant).delete()

    # AD-45: async PDF generation.
    from .tasks import after_admission_tasks
    after_admission_tasks.delay(applicant.id)

    logger.info(
        'Admitted applicant %s as student %s by user %s',
        applicant.applicant_code, student.student_id, admitted_by.id,
    )
    return student


def _stream_capacity(class_name, stream):
    """AD-41. Reads from an `academics.Stream` model when that app is
    added (SEAM_ACADEMICS); returns the configurable default constant
    until then. When academics lands, replace the body with an FK lookup
    on (class_name, stream) — nothing else in this file changes."""
    return DEFAULT_STREAM_CAPACITY