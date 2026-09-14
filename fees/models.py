from django.db import models
from djmoney.models.fields import MoneyField


class FeeStructure(models.Model):
    class_name = models.CharField(max_length=10)
    stream = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B')])
    term = models.CharField(max_length=30, default='Term 1')
    total_amount = MoneyField(max_digits=12, decimal_places=2, default_currency='MWK')

    class Meta:
        unique_together = ('class_name', 'stream', 'term')

    def __str__(self):
        return f'{self.class_name}{self.stream} - {self.term}: MK {self.total_amount}'


class Discount(models.Model):
    """FP-33/34/35/36: percentage/fixed discounts, bursaries and
    scholarships, auditable via simple_history and an explicit approver."""

    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage', 'Percentage'
        FIXED = 'fixed', 'Fixed Amount'

    class Kind(models.TextChoices):
        DISCOUNT = 'discount', 'Discount (e.g. sibling, staff child)'
        BURSARY = 'bursary', 'Bursary'
        SCHOLARSHIP = 'scholarship', 'Scholarship'

    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='discounts')
    kind = models.CharField(max_length=15, choices=Kind.choices, default=Kind.DISCOUNT)
    discount_type = models.CharField(max_length=10, choices=DiscountType.choices, default=DiscountType.PERCENTAGE)
    value = models.DecimalField(max_digits=12, decimal_places=2, help_text='Percentage (0-100) or a fixed MK amount.')
    sponsor_name = models.CharField(max_length=150, blank=True, help_text='NGO, government, church, etc.')
    reason = models.CharField(max_length=255, blank=True)
    approved_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='discounts_approved',
    )
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-effective_date']

    def __str__(self):
        return f'{self.get_kind_display()} for {self.student.full_name}: {self.value}{"%" if self.discount_type == self.DiscountType.PERCENTAGE else " MK"}'

    def amount_for(self, base_amount):
        if self.discount_type == self.DiscountType.PERCENTAGE:
            return (base_amount * self.value) / 100
        return min(self.value, base_amount)


class FeeTransaction(models.Model):
    class Method(models.TextChoices):
        MOBILE_MONEY = 'Mobile Money', 'Mobile Money'
        CASH = 'Cash', 'Cash'
        BANK_TRANSFER = 'Bank Transfer', 'Bank Transfer'
        ONLINE = 'Online', 'Online (Card/Mobile via gateway)'

    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='transactions')
    amount = MoneyField(max_digits=12, decimal_places=2, default_currency='MWK')
    date = models.DateField()
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.MOBILE_MONEY)
    receipt_no = models.CharField(max_length=30, unique=True)
    recorded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    # Populated when this receipt originated from an online gateway
    # payment (see payments.PaymentTransaction) rather than a manually
    # recorded cash/bank/mobile-money entry at the front desk.
    gateway = models.CharField(max_length=30, blank=True)
    gateway_reference = models.CharField(max_length=100, blank=True)
    # FP-24: payments are never deleted, only reversed.
    is_reversed = models.BooleanField(default=False)
    reversed_at = models.DateTimeField(null=True, blank=True)
    reversed_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reversals_made',
    )
    reversal_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'{self.receipt_no} - {self.student.full_name} - MK {self.amount}'

    def save(self, *args, **kwargs):
        if not self.receipt_no:
            last_id = FeeTransaction.objects.count() + 1
            self.receipt_no = f'RCP-{self.date.year}-{last_id:04d}'
        super().save(*args, **kwargs)

    def reverse(self, user, reason=''):
        """FP-24: void a payment without deleting it; rolls the amount
        back off the student's fees_paid total."""
        import datetime
        if self.is_reversed:
            return
        self.is_reversed = True
        self.reversed_at = datetime.datetime.now()
        self.reversed_by = user
        self.reversal_reason = reason
        self.save(update_fields=['is_reversed', 'reversed_at', 'reversed_by', 'reversal_reason'])
        self.student.fees_paid = self.student.fees_paid - self.amount
        self.student.save(update_fields=['fees_paid'])
