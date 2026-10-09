"""Celery tasks for the invitation flow (governance doc §4, §6).

SMS/email delivery is throttled separately in `notifications.tasks` — this
module just decides *what* to send and *to whom*, so the same task can be
used by both the single-invitation flow and the bulk admission import.
"""
from celery import shared_task
from django.conf import settings
from django.urls import reverse
from django.utils import timezone


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def deliver_invitation(self, invitation_id):
    from .models import InvitationToken
    from notifications.tasks import send_sms

    try:
        invitation = InvitationToken.objects.select_related('issued_by').get(id=invitation_id)
    except InvitationToken.DoesNotExist:
        return

    if not invitation.is_valid():
        return

    # Build the claim URL. `settings.SITE_URL` should be set in production;
    # in dev we fall back to a relative path the console backend prints.
    base = getattr(settings, 'SITE_URL', '').rstrip('/')
    path = reverse('accounts:claim_invitation', kwargs={'token': invitation.token})
    claim_url = f'{base}{path}' if base else path

    message = (
        f'Malawi School ERP — set up your account: {claim_url} '
        f'(valid until {invitation.expires_at:%d %b %Y})'
    )

    delivered = False
    if invitation.invited_phone:
        try:
            send_sms.delay(invitation.invited_phone, message)
            delivered = True
        except Exception as exc:  # noqa: BLE001
            raise self.retry(exc=exc)

    if invitation.invited_email:
        from django.core.mail import send_mail
        send_mail(
            'Malawi School ERP — set up your account',
            (
                f'Hello {invitation.invited_first_name or "there"},\n\n'
                f'Use the link below to set your password. It expires on '
                f'{invitation.expires_at:%d %b %Y}.\n\n{claim_url}\n'
            ),
            settings.DEFAULT_FROM_EMAIL,
            [invitation.invited_email],
            fail_silently=True,
        )
        delivered = True

    if delivered:
        invitation.delivered_at = timezone.now()
        invitation.delivery_method = (
            InvitationToken.DeliveryMethod.BOTH
            if invitation.invited_phone and invitation.invited_email
            else (InvitationToken.DeliveryMethod.SMS if invitation.invited_phone
                  else InvitationToken.DeliveryMethod.EMAIL)
        )
        invitation.save(update_fields=['delivered_at', 'delivery_method'])