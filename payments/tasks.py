"""
Celery tasks for payment gateway processing.

NFR: 'idempotency keys on mobile money callbacks to prevent duplicate
postings' - `apply_confirmed_payment` is safe to call more than once for
the same PaymentTransaction; it only posts a FeeTransaction the first
time a transaction flips to 'success'.
"""
import logging

from celery import shared_task
from django.db import transaction as db_transaction

logger = logging.getLogger(__name__)


@shared_task
def apply_confirmed_payment(payment_transaction_id):
    from .models import PaymentTransaction
    from fees.models import FeeTransaction
    from notifications.tasks import send_fee_reminder

    try:
        pt = PaymentTransaction.objects.select_related('student').get(id=payment_transaction_id)
    except PaymentTransaction.DoesNotExist:
        logger.warning('apply_confirmed_payment: PaymentTransaction %s not found', payment_transaction_id)
        return

    if pt.status != PaymentTransaction.Status.SUCCESS or pt.fee_transaction_id:
        # Not confirmed yet, or already posted - idempotent no-op.
        return

    with db_transaction.atomic():
        pt.refresh_from_db()
        if pt.fee_transaction_id:
            return  # another worker already posted this one
        fee_txn = FeeTransaction.objects.create(
            student=pt.student, amount=pt.amount, date=pt.updated_at.date(),
            method=FeeTransaction.Method.MOBILE_MONEY, gateway=pt.gateway,
            gateway_reference=pt.gateway_reference or pt.reference,
        )
        pt.fee_transaction = fee_txn
        pt.save(update_fields=['fee_transaction'])
        student = pt.student
        student.fees_paid = student.fees_paid + pt.amount.amount
        student.save(update_fields=['fees_paid'])

    if pt.student.balance > 0:
        send_fee_reminder.delay(pt.student.id)
    logger.info('Posted PayChangu payment %s as %s', pt.reference, fee_txn.receipt_no)


@shared_task
def verify_pending_payment(payment_transaction_id):
    """Polling fallback (NFR: 'polling every 6 hours' pattern from the
    MANEB doc, reused here) for when a webhook never arrives."""
    from .models import PaymentTransaction
    from .registry import get_gateway

    try:
        pt = PaymentTransaction.objects.get(id=payment_transaction_id)
    except PaymentTransaction.DoesNotExist:
        return
    if pt.status != PaymentTransaction.Status.PENDING:
        return

    gateway = get_gateway(pt.gateway)
    result = gateway.verify_payment(pt.gateway_reference or pt.reference)
    pt.raw_webhook_response = result.raw_response
    if result.status == 'success':
        pt.status = PaymentTransaction.Status.SUCCESS
        pt.save(update_fields=['status', 'raw_webhook_response'])
        apply_confirmed_payment.delay(pt.id)
    elif result.status == 'failed':
        pt.status = PaymentTransaction.Status.FAILED
        pt.save(update_fields=['status', 'raw_webhook_response'])
    else:
        pt.save(update_fields=['raw_webhook_response'])
