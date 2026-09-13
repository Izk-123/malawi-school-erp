import uuid

from django.conf import settings as dj_settings
from django.db import models


def generate_reference():
    return uuid.uuid4().hex


class PaymentTransaction(models.Model):
    """
    NFR: 'immutable audit trail', 'idempotency keys on mobile money
    callbacks to prevent duplicate postings'. One row per gateway attempt,
    regardless of which fee it's eventually applied against - kept
    separate from `fees.FeeTransaction` (the school's internal receipt
    ledger) so a failed/abandoned checkout never pollutes fee records,
    and so this table works the same regardless of which app initiates
    a payment (fees today; MANEB exam fees or anything else tomorrow).
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'

    reference = models.CharField(max_length=64, unique=True, default=generate_reference, editable=False)
    gateway = models.CharField(max_length=30, default='paychangu')
    gateway_reference = models.CharField(max_length=100, blank=True)
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='payment_transactions')
    initiated_by = models.ForeignKey(dj_settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='MWK')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    checkout_url = models.URLField(blank=True)
    raw_initiation_response = models.JSONField(null=True, blank=True)
    raw_webhook_response = models.JSONField(null=True, blank=True)
    fee_transaction = models.OneToOneField(
        'fees.FeeTransaction', on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_transaction',
        help_text='The internal receipt this gateway payment was posted as, once confirmed.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['status']), models.Index(fields=['gateway_reference'])]

    def __str__(self):
        return f'{self.gateway}:{self.reference} - {self.student.full_name} - MK {self.amount} ({self.status})'
