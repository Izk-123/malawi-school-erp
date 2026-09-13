"""
PayChangu gateway - the first concrete PaymentGateway implementation.

PayChangu (https://paychangu.com) is a Malawian payment aggregator
covering mobile money (Airtel Money, TNM Mpamba), cards, and bank
transfer behind a single checkout, which is why it's the pragmatic
"for now" choice: it already covers most of FP-17's payment methods
through one integration instead of building a separate integration per
mobile money operator.

API shape (per PayChangu's hosted checkout + webhook docs):
  - POST {base_url}/payment            -> initiate, returns a checkout_url
  - GET  {base_url}/verify-payment/<tx_ref>  -> poll status
  - Webhook: POST to our callback URL, signed with HMAC-SHA256 over the
    raw body using the webhook secret, sent in the `Signature` header.

If PayChangu changes field names or endpoints, only this file needs to
change - the rest of the app talks to `PaymentGateway`'s abstract
interface, not to PayChangu directly.
"""
import hashlib
import hmac
import json
import logging

import requests

from .base import PaymentGateway, PaymentInitiationResult, PaymentVerificationResult

logger = logging.getLogger(__name__)

STATUS_MAP = {
    'success': 'success',
    'successful': 'success',
    'completed': 'success',
    'failed': 'failed',
    'cancelled': 'failed',
    'pending': 'pending',
}


class PaychanguGateway(PaymentGateway):
    name = 'paychangu'

    def __init__(self, config: dict):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://api.paychangu.com')
        self.secret_key = config.get('secret_key', '')
        self.webhook_secret = config.get('webhook_secret', '')
        self.timeout = config.get('timeout', 15)

    def _headers(self):
        return {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def initiate_payment(self, *, amount, currency, reference, customer_name,
                          customer_email, customer_phone, callback_url, return_url) -> PaymentInitiationResult:
        first_name, _, last_name = customer_name.partition(' ')
        payload = {
            'amount': str(amount),
            'currency': currency,
            'tx_ref': reference,
            'email': customer_email or f'{reference}@no-email.mzuzusec.mw',
            'first_name': first_name or customer_name,
            'last_name': last_name or '-',
            'phone_number': customer_phone,
            'callback_url': callback_url,
            'return_url': return_url,
        }
        try:
            response = requests.post(
                f'{self.base_url}/payment', json=payload, headers=self._headers(), timeout=self.timeout,
            )
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.error('PayChangu initiate_payment failed: %s', exc)
            return PaymentInitiationResult(success=False, error=str(exc))

        if response.status_code >= 400 or data.get('status') != 'success':
            return PaymentInitiationResult(
                success=False, raw_response=data,
                error=data.get('message', f'PayChangu returned HTTP {response.status_code}'),
            )

        checkout_url = (data.get('data') or {}).get('checkout_url')
        return PaymentInitiationResult(
            success=True, checkout_url=checkout_url, gateway_reference=reference, raw_response=data,
        )

    def verify_payment(self, reference: str) -> PaymentVerificationResult:
        try:
            response = requests.get(
                f'{self.base_url}/verify-payment/{reference}', headers=self._headers(), timeout=self.timeout,
            )
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.error('PayChangu verify_payment failed: %s', exc)
            return PaymentVerificationResult(status='pending', raw_response={'error': str(exc)})

        inner = data.get('data') or {}
        status = STATUS_MAP.get(str(inner.get('status', '')).lower(), 'pending')
        return PaymentVerificationResult(
            status=status, amount=inner.get('amount'), gateway_reference=reference, raw_response=data,
        )

    def verify_webhook_signature(self, request) -> bool:
        if not self.webhook_secret:
            # No secret configured (e.g. local/dev) - accept, but this
            # should never be true in production; assign_role_permissions-
            # style .env checks are documented in the README.
            return True
        signature = request.headers.get('Signature', '')
        computed = hmac.new(
            self.webhook_secret.encode(), request.body, hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(signature, computed)

    def parse_webhook(self, request) -> PaymentVerificationResult:
        payload = json.loads(request.body or '{}')
        inner = payload.get('data', payload)
        status = STATUS_MAP.get(str(inner.get('status', '')).lower(), 'pending')
        return PaymentVerificationResult(
            status=status,
            amount=inner.get('amount'),
            gateway_reference=inner.get('tx_ref') or inner.get('reference'),
            raw_response=payload,
        )
