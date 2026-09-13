import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from accounts.mixins import RoleRequiredMixin
from students.models import Student
from .models import PaymentTransaction
from .registry import get_gateway, available_gateways
from .tasks import apply_confirmed_payment

logger = logging.getLogger(__name__)


class InitiatePaymentView(LoginRequiredMixin, RoleRequiredMixin, View):
    """FP-17/30: a parent (or admin, on a parent's behalf) starts an
    online payment for a student's outstanding balance."""
    allowed_roles = ['admin', 'parent']

    def get(self, request, student_id):
        student = get_object_or_404(Student, pk=student_id)
        if request.user.role == 'parent' and not student.guardians.filter(pk=request.user.pk).exists():
            messages.error(request, "That student isn't linked to your account.")
            return redirect('students:my_children')
        return render(request, 'payments/initiate.html', {
            'student': student, 'gateways': available_gateways(),
        })

    def post(self, request, student_id):
        student = get_object_or_404(Student, pk=student_id)
        if request.user.role == 'parent' and not student.guardians.filter(pk=request.user.pk).exists():
            messages.error(request, "That student isn't linked to your account.")
            return redirect('students:my_children')

        amount = request.POST.get('amount')
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            messages.error(request, 'Enter a valid amount.')
            return redirect('payments:initiate', student_id=student.id)
        if amount <= 0 or amount > float(student.balance):
            messages.error(request, f"Amount must be between MK 1 and the outstanding balance (MK {student.balance:,.2f}).")
            return redirect('payments:initiate', student_id=student.id)

        gateway_name = request.POST.get('gateway') or None
        gateway = get_gateway(gateway_name)

        pt = PaymentTransaction.objects.create(
            gateway=gateway_name or gateway.name, student=student, initiated_by=request.user,
            amount=amount, status=PaymentTransaction.Status.PENDING,
        )
        result = gateway.initiate_payment(
            amount=amount, currency='MWK', reference=pt.reference,
            customer_name=student.guardian_name or student.full_name,
            customer_email=getattr(request.user, 'email', ''),
            customer_phone=student.guardian_phone,
            callback_url=request.build_absolute_uri(reverse('payments:webhook', args=[pt.gateway])),
            return_url=request.build_absolute_uri(reverse('payments:return', args=[pt.reference])),
        )
        pt.raw_initiation_response = result.raw_response
        if result.gateway_reference:
            pt.gateway_reference = result.gateway_reference
        if not result.success:
            pt.status = PaymentTransaction.Status.FAILED
            pt.save()
            messages.error(request, f'Could not start payment: {result.error or "gateway error"}.')
            return redirect('payments:initiate', student_id=student.id)

        pt.checkout_url = result.checkout_url or ''
        pt.save()
        if pt.checkout_url:
            return redirect(pt.checkout_url)
        return redirect('payments:return', reference=pt.reference)


class PaymentReturnView(LoginRequiredMixin, View):
    """Where the payer lands back after the gateway checkout, regardless
    of outcome - actual confirmation always comes via the webhook (or the
    polling fallback), never trusted from this redirect alone."""

    def get(self, request, reference):
        pt = get_object_or_404(PaymentTransaction, reference=reference)
        return render(request, 'payments/return.html', {'transaction': pt})


@method_decorator(csrf_exempt, name='dispatch')
class PaymentWebhookView(View):
    """FP-26: async gateway callback. No login (the gateway calls this,
    not a browser) - integrity comes from signature verification, not
    session auth. Idempotent: safe to receive the same webhook twice."""

    def post(self, request, gateway_name):
        try:
            gateway = get_gateway(gateway_name)
        except ValueError:
            return HttpResponseBadRequest('Unknown gateway')

        if not gateway.verify_webhook_signature(request):
            logger.warning('Rejected webhook for %s: bad signature', gateway_name)
            return HttpResponseBadRequest('Invalid signature')

        result = gateway.parse_webhook(request)
        if not result.gateway_reference:
            return HttpResponseBadRequest('Missing reference')

        pt = PaymentTransaction.objects.filter(
            reference=result.gateway_reference,
        ).first() or PaymentTransaction.objects.filter(
            gateway_reference=result.gateway_reference,
        ).first()
        if not pt:
            logger.warning('Webhook for unknown reference %s', result.gateway_reference)
            return HttpResponseBadRequest('Unknown transaction')

        pt.raw_webhook_response = result.raw_response
        if result.status == 'success' and pt.status != PaymentTransaction.Status.SUCCESS:
            pt.status = PaymentTransaction.Status.SUCCESS
            pt.save(update_fields=['status', 'raw_webhook_response'])
            apply_confirmed_payment.delay(pt.id)
        elif result.status == 'failed':
            pt.status = PaymentTransaction.Status.FAILED
            pt.save(update_fields=['status', 'raw_webhook_response'])
        else:
            pt.save(update_fields=['raw_webhook_response'])

        return JsonResponse({'received': True})
