import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from accounts.mixins import RoleRequiredMixin
from students.models import Student
from notifications.tasks import notify_sickbay_referral
from .models import (
    StaffMember, StaffRoleAssignment, LeaveRequest, StaffAttendance,
    StaffAnnouncement, StaffTicket, Payslip, Book, BookLoan, VisitorLog,
    GatePass, PatrolLog, MedicalRecord, SickBayVisit, MedicationStock,
)
from .forms import (
    StaffMemberForm, StaffProfileForm, LeaveRequestForm, StaffTicketForm,
    BookForm, BookLoanForm, VisitorLogForm, GatePassForm, SickBayVisitForm,
    MedicalRecordForm, MedicationStockForm,
)
from .filters import StaffFilter


def _get_staff(request):
    return StaffMember.objects.filter(user=request.user).first()


# ============================================================
# Common (STF-01 to STF-10)
# ============================================================

class StaffListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = StaffMember
    template_name = 'staff/staff_list.html'
    context_object_name = 'staff_members'
    allowed_roles = ['admin', 'hr']

    def get_queryset(self):
        self.filterset = StaffFilter(self.request.GET, queryset=StaffMember.objects.all())
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter'] = self.filterset
        return ctx


class StaffPortalDashboardView(LoginRequiredMixin, RoleRequiredMixin, View):
    """STF-02: one dashboard per role, showing only role-relevant widgets."""
    allowed_roles = ['staff']

    def get(self, request):
        staff = _get_staff(request)
        if not staff:
            return render(request, 'staff/portal_dashboard.html', {'staff': None})

        roles = staff.role_codes
        context = {
            'staff': staff, 'roles': roles,
            'announcements': StaffAnnouncement.objects.all()[:5],
            'pending_leave': staff.leave_requests.filter(status='pending').count(),
            'today_attendance': StaffAttendance.objects.filter(staff=staff, date=datetime.date.today()).first(),
        }
        if 'bursar' in roles:
            from fees.models import FeeTransaction
            context['todays_collections'] = FeeTransaction.objects.filter(date=datetime.date.today(), is_reversed=False).count()
            context['defaulter_count'] = sum(1 for s in Student.objects.filter(status='active') if s.balance > 0)
        if 'librarian' in roles:
            context['overdue_loans'] = BookLoan.objects.filter(returned_date__isnull=True, due_date__lt=datetime.date.today()).count()
            context['todays_returns'] = BookLoan.objects.filter(returned_date=datetime.date.today()).count()
        if 'security' in roles:
            context['active_gate_passes'] = GatePass.objects.filter(status='out').count()
            context['visitors_today'] = VisitorLog.objects.filter(time_in__date=datetime.date.today()).count()
        if 'nurse' in roles:
            context['sickbay_today'] = SickBayVisit.objects.filter(visit_date__date=datetime.date.today()).count()
            context['low_stock'] = [m for m in MedicationStock.objects.all() if m.needs_reorder]
        if 'ict' in roles or 'groundskeeper' in roles or 'lab_tech' in roles:
            context['open_tickets'] = StaffTicket.objects.filter(assigned_to=staff, status='open').count()
        if 'hr' in roles:
            context['leave_queue'] = LeaveRequest.objects.filter(status='pending').count()

        return render(request, 'staff/portal_dashboard.html', context)


class MyProfileView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    """STF-03."""
    form_class = StaffProfileForm
    template_name = 'staff/my_profile.html'
    success_url = reverse_lazy('staff:my_profile')
    allowed_roles = ['staff']

    def get_object(self):
        return _get_staff(self.request)

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated.')
        return super().form_valid(form)


class MyLeaveView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    """STF-04."""
    model = LeaveRequest
    template_name = 'staff/my_leave.html'
    context_object_name = 'leave_requests'
    allowed_roles = ['staff']

    def get_queryset(self):
        staff = _get_staff(self.request)
        return LeaveRequest.objects.filter(staff=staff) if staff else LeaveRequest.objects.none()


class RequestLeaveView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    form_class = LeaveRequestForm
    template_name = 'staff/leave_form.html'
    success_url = reverse_lazy('staff:my_leave')
    allowed_roles = ['staff']

    def form_valid(self, form):
        form.instance.staff = _get_staff(self.request)
        messages.success(self.request, 'Leave request submitted.')
        return super().form_valid(form)


class LeaveApprovalView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    """STF-92: HR/admin approval queue."""
    model = LeaveRequest
    template_name = 'staff/leave_approval.html'
    context_object_name = 'leave_requests'
    allowed_roles = ['admin', 'hr']

    def get_queryset(self):
        return LeaveRequest.objects.filter(status='pending')


class DecideLeaveView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ['admin', 'hr']

    def post(self, request, pk):
        import django.utils.timezone as tz
        leave = get_object_or_404(LeaveRequest, pk=pk)
        decision = request.POST.get('decision')
        if decision in ('approved', 'rejected'):
            leave.status = decision
            leave.approved_by = request.user
            leave.decided_at = tz.now()
            leave.save()
            messages.success(request, f'Leave request {decision}.')
        return redirect('staff:leave_approval')


class ClockInOutView(LoginRequiredMixin, RoleRequiredMixin, View):
    """STF-07."""
    allowed_roles = ['staff']

    def post(self, request):
        staff = _get_staff(request)
        if not staff:
            messages.error(request, 'No staff profile linked to your account.')
            return redirect('staff:dashboard')
        record, _ = StaffAttendance.objects.get_or_create(staff=staff, date=datetime.date.today())
        now = datetime.datetime.now().time()
        if not record.clock_in:
            record.clock_in = now
            messages.success(request, f'Clocked in at {now:%H:%M}.')
        elif not record.clock_out:
            record.clock_out = now
            messages.success(request, f'Clocked out at {now:%H:%M}.')
        else:
            messages.info(request, 'Already clocked in and out today.')
        record.save()
        return redirect('staff:dashboard')


class AnnouncementListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    """STF-08."""
    model = StaffAnnouncement
    template_name = 'staff/announcements.html'
    context_object_name = 'announcements'
    allowed_roles = ['admin', 'staff']


class PostAnnouncementView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = StaffAnnouncement
    fields = ['title', 'body', 'pinned']
    template_name = 'staff/announcement_form.html'
    success_url = reverse_lazy('staff:announcements')
    allowed_roles = ['admin']

    def form_valid(self, form):
        form.instance.posted_by = self.request.user
        return super().form_valid(form)


class TicketListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    """STF-09/53/59/71/72/74: the shared incident/maintenance/ICT/lab ticket queue."""
    model = StaffTicket
    template_name = 'staff/ticket_list.html'
    context_object_name = 'tickets'
    allowed_roles = ['admin', 'staff']

    def get_queryset(self):
        qs = StaffTicket.objects.all()
        ticket_type = self.request.GET.get('type')
        if ticket_type:
            qs = qs.filter(ticket_type=ticket_type)
        return qs


class RaiseTicketView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    form_class = StaffTicketForm
    template_name = 'staff/ticket_form.html'
    success_url = reverse_lazy('staff:tickets')
    allowed_roles = ['admin', 'staff']

    def form_valid(self, form):
        form.instance.raised_by = self.request.user
        messages.success(self.request, 'Report submitted.')
        return super().form_valid(form)


class ResolveTicketView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ['admin', 'staff']

    def post(self, request, pk):
        import django.utils.timezone as tz
        ticket = get_object_or_404(StaffTicket, pk=pk)
        ticket.status = StaffTicket.Status.RESOLVED
        ticket.resolved_at = tz.now()
        ticket.save()
        messages.success(request, 'Ticket marked resolved.')
        return redirect('staff:tickets')


class MyPayslipsView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    """STF-05."""
    model = Payslip
    template_name = 'staff/my_payslips.html'
    context_object_name = 'payslips'
    allowed_roles = ['staff']

    def get_queryset(self):
        staff = _get_staff(self.request)
        return Payslip.objects.filter(staff=staff) if staff else Payslip.objects.none()


class PayslipPDFView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ['staff']

    def get(self, request, pk):
        from common.pdf import render_simple_document
        payslip = get_object_or_404(Payslip, pk=pk)
        staff = _get_staff(request)
        if payslip.staff_id != (staff.id if staff else None):
            messages.error(request, "That payslip isn't linked to your account.")
            return redirect('staff:my_payslips')
        lines = [
            ('Staff', payslip.staff.full_name), ('Period', f'{payslip.month}/{payslip.year}'),
            ('Gross Pay', f'MK {payslip.gross_pay:,.2f}'), ('Deductions', f'MK {payslip.deductions:,.2f}'),
            ('Net Pay', f'MK {payslip.net_pay:,.2f}'),
        ]
        pdf_bytes = render_simple_document(
            title='Payslip', subtitle=None, lines=lines,
            footer='This is a simplified payslip; full PAYE/pension calculation is a future finance-module addition.',
        )
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="payslip_{payslip.month}_{payslip.year}.pdf"'
        return response


def _require_staff_role(request, role_code):
    """Sub-role check within the 'staff' account role (librarian, security,
    nurse, etc. are StaffRoleAssignment rows, not separate User.role
    values) - admins bypass since they can act as any portal."""
    if request.user.is_superuser or request.user.role == 'admin':
        return True
    staff = _get_staff(request)
    return bool(staff and staff.has_role(role_code))


# ============================================================
# Librarian portal (STF-21 to STF-28)
# ============================================================

class BookListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = Book
    template_name = 'staff/librarian/book_list.html'
    context_object_name = 'books'
    allowed_roles = ['admin', 'staff']

    def dispatch(self, request, *args, **kwargs):
        if not _require_staff_role(request, 'librarian'):
            messages.error(request, "You don't have librarian access.")
            return redirect('staff:dashboard')
        return super().dispatch(request, *args, **kwargs)


class BookCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    form_class = BookForm
    template_name = 'staff/librarian/book_form.html'
    success_url = reverse_lazy('staff:book_list')
    allowed_roles = ['admin', 'staff']

    def dispatch(self, request, *args, **kwargs):
        if not _require_staff_role(request, 'librarian'):
            messages.error(request, "You don't have librarian access.")
            return redirect('staff:dashboard')
        return super().dispatch(request, *args, **kwargs)


class LoanListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = BookLoan
    template_name = 'staff/librarian/loan_list.html'
    context_object_name = 'loans'
    allowed_roles = ['admin', 'staff']

    def dispatch(self, request, *args, **kwargs):
        if not _require_staff_role(request, 'librarian'):
            messages.error(request, "You don't have librarian access.")
            return redirect('staff:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = BookLoan.objects.select_related('book', 'student', 'staff')
        if self.request.GET.get('overdue'):
            qs = [l for l in qs if l.is_overdue]
        return qs


class IssueBookView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    form_class = BookLoanForm
    template_name = 'staff/librarian/loan_form.html'
    success_url = reverse_lazy('staff:loan_list')
    allowed_roles = ['admin', 'staff']

    def dispatch(self, request, *args, **kwargs):
        if not _require_staff_role(request, 'librarian'):
            messages.error(request, "You don't have librarian access.")
            return redirect('staff:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.issued_by = _get_staff(self.request)
        messages.success(self.request, 'Book issued.')
        return super().form_valid(form)


class ReturnBookView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ['admin', 'staff']

    def post(self, request, pk):
        if not _require_staff_role(request, 'librarian'):
            messages.error(request, "You don't have librarian access.")
            return redirect('staff:dashboard')
        loan = get_object_or_404(BookLoan, pk=pk)
        loan.returned_date = datetime.date.today()
        loan.save()
        fine = loan.fine_amount
        if fine:
            messages.warning(request, f'Book returned. Overdue fine: MK {fine}.')
        else:
            messages.success(request, 'Book returned, no fine.')
        return redirect('staff:loan_list')


# ============================================================
# Security portal (STF-36 to STF-42)
# ============================================================

class VisitorLogListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = VisitorLog
    template_name = 'staff/security/visitor_list.html'
    context_object_name = 'visitors'
    allowed_roles = ['admin', 'staff']

    def dispatch(self, request, *args, **kwargs):
        if not _require_staff_role(request, 'security'):
            messages.error(request, "You don't have security access.")
            return redirect('staff:dashboard')
        return super().dispatch(request, *args, **kwargs)


class LogVisitorView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    form_class = VisitorLogForm
    template_name = 'staff/security/visitor_form.html'
    success_url = reverse_lazy('staff:visitor_list')
    allowed_roles = ['admin', 'staff']

    def dispatch(self, request, *args, **kwargs):
        if not _require_staff_role(request, 'security'):
            messages.error(request, "You don't have security access.")
            return redirect('staff:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.recorded_by = _get_staff(self.request)
        return super().form_valid(form)


class SignOutVisitorView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ['admin', 'staff']

    def post(self, request, pk):
        import django.utils.timezone as tz
        visitor = get_object_or_404(VisitorLog, pk=pk)
        visitor.time_out = tz.now()
        visitor.save()
        messages.success(request, f'{visitor.name} signed out.')
        return redirect('staff:visitor_list')


class GatePassListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = GatePass
    template_name = 'staff/security/gate_pass_list.html'
    context_object_name = 'gate_passes'
    allowed_roles = ['admin', 'staff']

    def dispatch(self, request, *args, **kwargs):
        if not _require_staff_role(request, 'security'):
            messages.error(request, "You don't have security access.")
            return redirect('staff:dashboard')
        return super().dispatch(request, *args, **kwargs)


class IssueGatePassView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    form_class = GatePassForm
    template_name = 'staff/security/gate_pass_form.html'
    success_url = reverse_lazy('staff:gate_pass_list')
    allowed_roles = ['admin', 'staff']

    def form_valid(self, form):
        form.instance.issued_by = _get_staff(self.request)
        form.instance.approved_by = self.request.user
        return super().form_valid(form)


class MarkGatePassView(LoginRequiredMixin, RoleRequiredMixin, View):
    """Toggle issued -> out -> returned."""
    allowed_roles = ['admin', 'staff']

    def post(self, request, pk):
        import django.utils.timezone as tz
        gp = get_object_or_404(GatePass, pk=pk)
        if gp.status == GatePass.Status.ISSUED:
            gp.status = GatePass.Status.OUT
            gp.time_out = tz.now()
        elif gp.status == GatePass.Status.OUT:
            gp.status = GatePass.Status.RETURNED
            gp.time_in = tz.now()
        gp.save()
        return redirect('staff:gate_pass_list')


# ============================================================
# Nurse portal (STF-43 to STF-51)
# ============================================================

class SickBayVisitListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = SickBayVisit
    template_name = 'staff/nurse/visit_list.html'
    context_object_name = 'visits'
    allowed_roles = ['admin', 'staff']

    def dispatch(self, request, *args, **kwargs):
        if not _require_staff_role(request, 'nurse'):
            messages.error(request, "You don't have nurse/matron access.")
            return redirect('staff:dashboard')
        return super().dispatch(request, *args, **kwargs)


class RecordSickBayVisitView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    form_class = SickBayVisitForm
    template_name = 'staff/nurse/visit_form.html'
    success_url = reverse_lazy('staff:sickbay_list')
    allowed_roles = ['admin', 'staff']

    def dispatch(self, request, *args, **kwargs):
        if not _require_staff_role(request, 'nurse'):
            messages.error(request, "You don't have nurse/matron access.")
            return redirect('staff:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.nurse = _get_staff(self.request)
        response = super().form_valid(form)
        if form.instance.referred:
            notify_sickbay_referral.delay(form.instance.id)
        messages.success(self.request, 'Sick bay visit recorded.')
        return response


class MedicalRecordUpdateView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ['admin', 'staff']

    def dispatch(self, request, *args, **kwargs):
        if not _require_staff_role(request, 'nurse'):
            messages.error(request, "You don't have nurse/matron access.")
            return redirect('staff:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, student_id):
        student = get_object_or_404(Student, pk=student_id)
        record, _ = MedicalRecord.objects.get_or_create(student=student)
        form = MedicalRecordForm(instance=record)
        return render(request, 'staff/nurse/medical_record_form.html', {'form': form, 'student': student})

    def post(self, request, student_id):
        student = get_object_or_404(Student, pk=student_id)
        record, _ = MedicalRecord.objects.get_or_create(student=student)
        form = MedicalRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, 'Medical record updated.')
            return redirect('staff:sickbay_list')
        return render(request, 'staff/nurse/medical_record_form.html', {'form': form, 'student': student})


class MedicationStockListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = MedicationStock
    template_name = 'staff/nurse/stock_list.html'
    context_object_name = 'stock_items'
    allowed_roles = ['admin', 'staff']

    def dispatch(self, request, *args, **kwargs):
        if not _require_staff_role(request, 'nurse'):
            messages.error(request, "You don't have nurse/matron access.")
            return redirect('staff:dashboard')
        return super().dispatch(request, *args, **kwargs)


class MedicationStockCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    form_class = MedicationStockForm
    template_name = 'staff/nurse/stock_form.html'
    success_url = reverse_lazy('staff:medication_stock')
    allowed_roles = ['admin', 'staff']
