"""
Pluggable payment gateway interface (FP-17/26, NFR: 'no direct card data,
tokenize via provider', scalability: 'Celery workers for mobile money
callbacks').

Every gateway (PayChangu today; Airtel Money, TNM Mpamba, or a bank
aggregator tomorrow) implements this same three-method contract. Callers
never talk to a gateway SDK directly - they go through
`payments.registry.get_gateway(name)`, so switching or adding a provider
never touches `fees` app code.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


@dataclass
class PaymentInitiationResult:
    """What every gateway returns after starting a payment."""
    success: bool
    checkout_url: Optional[str] = None       # where to redirect the payer, if any
    gateway_reference: Optional[str] = None  # the gateway's own transaction id
    raw_response: dict = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class PaymentVerificationResult:
    """What every gateway returns when asked 'did this payment succeed?'."""
    status: str  # one of PaymentTransaction.Status values
    amount: Optional[Decimal] = None
    gateway_reference: Optional[str] = None
    raw_response: dict = field(default_factory=dict)


class PaymentGateway:
    """Abstract base every concrete gateway must implement."""
    name = 'base'

    def __init__(self, config: dict):
        self.config = config

    def initiate_payment(self, *, amount: Decimal, currency: str, reference: str,
                          customer_name: str, customer_email: str, customer_phone: str,
                          callback_url: str, return_url: str) -> PaymentInitiationResult:
        """Start a payment; typically returns a checkout URL to redirect the payer to."""
        raise NotImplementedError

    def verify_payment(self, reference: str) -> PaymentVerificationResult:
        """Poll the gateway for the current status of a previously-initiated payment."""
        raise NotImplementedError

    def verify_webhook_signature(self, request) -> bool:
        """Check that an incoming webhook actually came from this gateway."""
        raise NotImplementedError

    def parse_webhook(self, request) -> PaymentVerificationResult:
        """Turn a verified webhook payload into a PaymentVerificationResult."""
        raise NotImplementedError
