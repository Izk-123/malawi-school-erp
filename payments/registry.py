"""
Gateway factory. Adding a new provider later (Airtel Money direct, TNM
Mpamba direct, a bank aggregator, etc.) means: write a class implementing
`PaymentGateway`, register it here, add its config block to
`settings.PAYMENT_GATEWAYS`. Nothing in `fees` views/templates changes.
"""
from django.conf import settings

from .gateways.paychangu import PaychanguGateway

GATEWAY_CLASSES = {
    'paychangu': PaychanguGateway,
    # 'airtel_money': AirtelMoneyGateway,   # future
    # 'tnm_mpamba': TnmMpambaGateway,       # future
}


def get_gateway(name: str = None):
    """Returns a configured gateway instance. Defaults to
    settings.DEFAULT_PAYMENT_GATEWAY ('paychangu' for now)."""
    name = name or settings.DEFAULT_PAYMENT_GATEWAY
    gateway_cls = GATEWAY_CLASSES.get(name)
    if not gateway_cls:
        raise ValueError(f"Unknown payment gateway '{name}'. Registered: {list(GATEWAY_CLASSES)}")
    config = settings.PAYMENT_GATEWAYS.get(name, {})
    return gateway_cls(config)


def available_gateways():
    """Gateways that are registered in code, enabled, AND actually
    configured with credentials - used to build the 'pay online with...'
    choice list. A gateway enabled in settings but missing its secret key
    is treated as unavailable so parents see a clear 'not configured yet'
    message instead of clicking through to a guaranteed API failure."""
    return [
        name for name in GATEWAY_CLASSES
        if settings.PAYMENT_GATEWAYS.get(name, {}).get('enabled', False)
        and settings.PAYMENT_GATEWAYS.get(name, {}).get('secret_key')
    ]
