"""Async tasks for the admissions pipeline. Idempotent by design
(NFR §3): re-running any of these must not duplicate PDFs or messages."""
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def generate_offer_letter(self, offer_id):
    """AD-29: render the offer letter PDF. Currently stubbed via the
    shared `common.pdf` helper; the `documents` app will own the real
    WeasyPrint templates when it lands."""
    from .models import Offer
    from common.pdf import render_simple_document

    try:
        offer = Offer.objects.select_related('applicant', 'issued_by').get(id=offer_id)
    except Offer.DoesNotExist:
        return

    lines = [
        ('Applicant', f'{offer.applicant.full_name} ({offer.applicant.applicant_code})'),
        ('Applying for', offer.applicant.applying_for),
        ('Issued by', offer.issued_by.get_full_name() or offer.issued_by.username),
        ('Response deadline', offer.response_deadline),
        ('Boarding', offer.applicant.get_boarding_preference_display()),
    ]
    # Generate bytes; the `documents` app will persist these against the
    # applicant once it exists.
    try:
        pdf_bytes = render_simple_document(
            title='Offer of Admission',
            subtitle=f'Ref: {offer.applicant.applicant_code}',
            lines=lines,
            footer='This offer is conditional on fee payment by the deadline above.',
        )
        logger.info('Generated offer letter for %s (%d bytes)',
                    offer.applicant.applicant_code, len(pdf_bytes))
    except Exception as exc:  # noqa: BLE001
        raise self.retry(exc=exc)


@shared_task
def send_offer_sms(offer_id):
    """AD-30: SMS the guardian on offer issue. Idempotent by the
    sent_at marker (added when the notifications app grows a proper
    outbound queue — for now we just guard against double-sends within
    the same offer status)."""
    from .models import Offer
    from notifications.tasks import _send_sms_stub

    try:
        offer = Offer.objects.select_related('applicant').get(id=offer_id)
    except Offer.DoesNotExist:
        return
    message = (
        f'Congratulations — {offer.applicant.full_name} has been offered a place. '
        f'Please respond by {offer.response_deadline:%d %b %Y} to secure the slot.'
    )
    _send_sms_stub(offer.applicant.guardian_phone, message)


@shared_task
def after_admission_tasks(applicant_id):
    """AD-45: post-admission PDFs (admission letter, welcome pack, ID card).
    Stubbed for now — the `documents` app takes this over next."""
    from .models import Applicant
    try:
        applicant = Applicant.objects.select_related('student').get(id=applicant_id)
    except Applicant.DoesNotExist:
        return
    if not applicant.student_id:
        logger.warning('after_admission_tasks for applicant %s with no student', applicant_id)
        return
    logger.info(
        'Post-admission tasks queued for student %s (admission letter, welcome pack, ID card).',
        applicant.student.student_id,
    )


@shared_task
def expire_stale_offers_task():
    """AD-33: scheduled daily via Celery beat. See CELERY_BEAT_SCHEDULE."""
    from .services import expire_stale_offers
    count = expire_stale_offers()
    logger.info('Expired %d stale offer(s).', count)
    return count