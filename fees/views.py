import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView

from accounts.mixins import RoleRequiredMixin
from students.models import Student
from notifications.tasks import send_fee_reminder
from .models import FeeTransaction, Discount
from .forms import RecordPaymentForm


class FeeListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = Student
    template_name = 'fees/fee_list.html'
    context_object_name = 'students'
    allowed_roles = ['admin', 'parent']

    def get_queryset(self):
        if self.request.user.role == 'parent':
            return Student.objects.filter(guardians=self.request.user)
        return Student.objects.all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['transactions'] = FeeTransaction.objects.filter(is_reversed=False).select_related('student')[:20]
        students = ctx['students']
        total_expected = sum(s.fees_total for s in students)
        total_paid = sum(s.fees_paid for s in students)
        ctx['total_expected'] = total_expected
        ctx['total_paid'] = total_paid
        ctx['collection_rate'] = round((total_paid / total_expected) * 100) if total_expected else 0
        return ctx


class RecordPaymentView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = FeeTransaction
    form_class = RecordPaymentForm
    template_name = 'fees/payment_form.html'
    success_url = reverse_lazy('fees:list')
    allowed_roles = ['admin']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        student_id = self.request.GET.get('student')
        kwargs['student_queryset'] = (
            Student.objects.filter(pk=student_id) if student_id else Student.objects.all()
        )
        return kwargs

    def form_valid(self, form):
        form.instance.recorded_by = self.request.user
        response = super().form_valid(form)
        student = form.instance.student
        student.fees_paid += form.instance.amount
        student.save(update_fields=['fees_paid'])
        if student.balance > 0:
            send_fee_reminder.delay(student.id)
        messages.success(self.request, f'Payment of MK {form.instance.amount:,.2f} recorded. Receipt {form.instance.receipt_no}.')
        return response


class ReceiptView(LoginRequiredMixin, RoleRequiredMixin, View):
    """FP-19/20: a printable receipt for a single payment."""
    allowed_roles = ['admin', 'parent', 'student']

    def get(self, request, pk):
        txn = get_object_or_404(FeeTransaction, pk=pk)
        if request.user.role == 'parent' and not txn.student.guardians.filter(pk=request.user.pk).exists():
            messages.error(request, "That receipt isn't linked to your account.")
            return redirect('fees:list')
        if request.user.role == 'student' and txn.student.user_id != request.user.id:
            messages.error(request, "That receipt isn't linked to your account.")
            return redirect('fees:my_fees')
        return render(request, 'fees/receipt.html', {'txn': txn})


class ReversePaymentView(LoginRequiredMixin, RoleRequiredMixin, View):
    """FP-24: void a payment (never delete), with a reason on record."""
    allowed_roles = ['admin']

    def post(self, request, pk):
        txn = get_object_or_404(FeeTransaction, pk=pk)
        reason = request.POST.get('reason', '')
        if txn.is_reversed:
            messages.warning(request, 'That payment was already reversed.')
        else:
            txn.reverse(request.user, reason=reason)
            messages.success(request, f'Payment {txn.receipt_no} reversed.')
        return redirect('fees:list')


class AgeingReportView(LoginRequiredMixin, RoleRequiredMixin, View):
    """FP-32: ageing buckets for outstanding balances."""
    allowed_roles = ['admin']

    def get(self, request):
        today = datetime.date.today()
        buckets = {'0-30': [], '31-60': [], '61-90': [], '90+': []}
        for s in Student.objects.filter(status='active'):
            if s.balance <= 0:
                continue
            last_payment = s.transactions.filter(is_reversed=False).order_by('-date').first()
            reference_date = last_payment.date if last_payment else s.enrolled_on
            days = (today - reference_date).days
            if days <= 30:
                buckets['0-30'].append(s)
            elif days <= 60:
                buckets['31-60'].append(s)
            elif days <= 90:
                buckets['61-90'].append(s)
            else:
                buckets['90+'].append(s)
        totals = {k: sum(s.balance for s in v) for k, v in buckets.items()}
        return render(request, 'fees/ageing_report.html', {'buckets': buckets, 'totals': totals})


class DefaultersReportView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    """FP-42: class-wise fee defaulters."""
    model = Student
    template_name = 'fees/defaulters_report.html'
    context_object_name = 'students'
    allowed_roles = ['admin']

    def get_queryset(self):
        qs = Student.objects.filter(status='active')
        class_filter = self.request.GET.get('class_name')
        if class_filter:
            qs = qs.filter(class_name=class_filter)
        return sorted([s for s in qs if s.balance > 0], key=lambda s: -s.balance)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['classes'] = Student.objects.values_list('class_name', flat=True).distinct()
        return ctx


class DailyCollectionReportView(LoginRequiredMixin, RoleRequiredMixin, View):
    """FP-27/40: end-of-day cashier report, by method and officer."""
    allowed_roles = ['admin']

    def get(self, request):
        date_str = request.GET.get('date') or datetime.date.today().isoformat()
        date = datetime.date.fromisoformat(date_str)
        txns = FeeTransaction.objects.filter(date=date, is_reversed=False).select_related('student', 'recorded_by')
        by_method = {}
        for t in txns:
            by_method.setdefault(t.method, []).append(t)
        totals_by_method = {m: sum(t.amount for t in items) for m, items in by_method.items()}
        return render(request, 'fees/daily_collection_report.html', {
            'date': date, 'by_method': by_method, 'totals_by_method': totals_by_method,
            'grand_total': sum(totals_by_method.values()),
        })


class ExportTransactionsView(LoginRequiredMixin, RoleRequiredMixin, View):
    """FP-44: export the transaction ledger to CSV."""
    allowed_roles = ['admin']

    def get(self, request):
        import csv
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="fee_transactions.csv"'
        writer = csv.writer(response)
        writer.writerow(['Receipt No', 'Student', 'Amount', 'Date', 'Method', 'Gateway', 'Reversed'])
        for t in FeeTransaction.objects.select_related('student'):
            writer.writerow([t.receipt_no, t.student.full_name, t.amount, t.date, t.method, t.gateway, t.is_reversed])
        return response


class MyFeesView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ['student']

    def get(self, request):
        student = Student.objects.filter(user=request.user).first()
        transactions = FeeTransaction.objects.filter(student=student) if student else []
        return render(request, 'fees/my_fees.html', {'student': student, 'transactions': transactions})
