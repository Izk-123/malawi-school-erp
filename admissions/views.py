import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.mixins import AnyOfMixin, HasAnyGroupMixin
from . import services
from .filters import ApplicantFilter, EnquiryFilter
from .forms import (
    AdmitForm, ApplicantForm, DocumentAttachmentForm, EnquiryForm,
    EntranceExamForm, ExamAssignmentForm, ExamMarkForm, InterviewForm,
    OfferIssueForm, PriorityFlagForm,
)
from .models import (
    Applicant, ApplicantPriority, DocumentAttachment, Enquiry,
    EntranceExam, ExamAssignment, ExamMark, Interview, Offer, WaitlistEntry,
)


# ── Role shortcuts ──────────────────────────────────────────────────
CLERK_GROUPS = ['registry_clerk']
HR_GROUPS = ['hr_officer']
HEAD_GROUPS = ['head_teacher']
OFFICE_GROUPS = CLERK_GROUPS + HR_GROUPS + HEAD_GROUPS


def _can_offer(user):
    return user.is_superuser or user.groups.filter(name__in=HEAD_GROUPS).exists() or user.role == 'admin'


# ── Dashboard (AD-53/54/55/56) ──────────────────────────────────────
class AdmissionsDashboardView(LoginRequiredMixin, HasAnyGroupMixin, View):
    required_groups = OFFICE_GROUPS

    def get(self, request):
        counts = {
            'enquiries': Enquiry.objects.count(),
            'new_enquiries': Enquiry.objects.filter(status=Enquiry.Status.NEW).count(),
            'applicants': Applicant.objects.count(),
            'exam_completed': Applicant.objects.filter(status=Applicant.Status.EXAM_COMPLETED).count(),
            'interviewed': Applicant.objects.filter(status=Applicant.Status.INTERVIEWED).count(),
            'offered': Applicant.objects.filter(status=Applicant.Status.OFFERED).count(),
            'admitted': Applicant.objects.filter(status=Applicant.Status.ADMITTED).count(),
            'waitlisted': WaitlistEntry.objects.count(),
        }
        conversion_rate = (
            round(counts['admitted'] / counts['applicants'] * 100, 1)
            if counts['applicants'] else 0
        )
        sources = (
            Enquiry.objects.values('source')
            .annotate(total=Count('id'),
                      converted=Count('id', filter=Q(status=Enquiry.Status.CONVERTED)))
            .order_by('-total')
        )
        recent = Applicant.objects.order_by('-created_at')[:8]
        return render(request, 'admissions/dashboard.html', {
            'counts': counts,
            'conversion_rate': conversion_rate,
            'sources': sources,
            'recent': recent,
        })


# ── Enquiry CRUD (AD-01..AD-07) ─────────────────────────────────────
class EnquiryListView(LoginRequiredMixin, HasAnyGroupMixin, ListView):
    model = Enquiry
    template_name = 'admissions/enquiry_list.html'
    context_object_name = 'enquiries'
    paginate_by = 30
    required_groups = OFFICE_GROUPS

    def get_queryset(self):
        qs = Enquiry.objects.select_related('created_by', 'followed_up_by')
        self.filterset = EnquiryFilter(self.request.GET, queryset=qs)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter'] = self.filterset
        return ctx


class EnquiryCreateView(LoginRequiredMixin, HasAnyGroupMixin, CreateView):
    model = Enquiry
    form_class = EnquiryForm
    template_name = 'admissions/enquiry_form.html'
    success_url = reverse_lazy('admissions:enquiry_list')
    required_groups = OFFICE_GROUPS

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Enquiry recorded.')
        return super().form_valid(form)


class EnquiryUpdateView(LoginRequiredMixin, HasAnyGroupMixin, UpdateView):
    model = Enquiry
    form_class = EnquiryForm
    template_name = 'admissions/enquiry_form.html'
    success_url = reverse_lazy('admissions:enquiry_list')
    required_groups = OFFICE_GROUPS


class EnquiryDetailView(LoginRequiredMixin, HasAnyGroupMixin, DetailView):
    model = Enquiry
    template_name = 'admissions/enquiry_detail.html'
    context_object_name = 'enquiry'
    required_groups = OFFICE_GROUPS


class ConvertEnquiryView(LoginRequiredMixin, HasAnyGroupMixin, View):
    required_groups = OFFICE_GROUPS

    def post(self, request, pk):
        enquiry = get_object_or_404(Enquiry, pk=pk)
        try:
            applicant = services.convert_enquiry_to_applicant(
                enquiry, created_by=request.user,
            )
            messages.success(request, f'Converted to applicant {applicant.applicant_code}.')
            return redirect('admissions:applicant_detail', pk=applicant.pk)
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('admissions:enquiry_detail', pk=pk)


# ── Applicant CRUD (AD-08..AD-15) ───────────────────────────────────
class ApplicantListView(LoginRequiredMixin, HasAnyGroupMixin, ListView):
    model = Applicant
    template_name = 'admissions/applicant_list.html'
    context_object_name = 'applicants'
    paginate_by = 30
    required_groups = OFFICE_GROUPS

    def get_queryset(self):
        qs = Applicant.objects.select_related('enquiry', 'student').prefetch_related('priority_flags')
        self.filterset = ApplicantFilter(self.request.GET, queryset=qs)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter'] = self.filterset
        return ctx


class ApplicantCreateView(LoginRequiredMixin, HasAnyGroupMixin, CreateView):
    model = Applicant
    form_class = ApplicantForm
    template_name = 'admissions/applicant_form.html'
    success_url = reverse_lazy('admissions:applicant_list')
    required_groups = OFFICE_GROUPS

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        services._auto_detect_priorities(self.object)
        services.recompute_applicant_score(self.object)
        messages.success(self.request, f'Applicant {self.object.applicant_code} created.')
        return response


class ApplicantUpdateView(LoginRequiredMixin, HasAnyGroupMixin, UpdateView):
    model = Applicant
    form_class = ApplicantForm
    template_name = 'admissions/applicant_form.html'
    required_groups = OFFICE_GROUPS

    def get_success_url(self):
        return reverse('admissions:applicant_detail', kwargs={'pk': self.object.pk})


class ApplicantDetailView(LoginRequiredMixin, HasAnyGroupMixin, DetailView):
    """AD-14 + guided workflow: the timeline shown here is the core of the
    usability NFR ('vertical timeline with current stage and next action')."""
    model = Applicant
    template_name = 'admissions/applicant_detail.html'
    context_object_name = 'applicant'
    required_groups = OFFICE_GROUPS

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        a = self.object

        stages = [
            ('Applied', Applicant.Status.APPLIED, 'bi-file-earmark-text'),
            ('Exam', Applicant.Status.EXAM_COMPLETED, 'bi-pencil-square'),
            ('Interview', Applicant.Status.INTERVIEWED, 'bi-people'),
            ('Offered', Applicant.Status.OFFERED, 'bi-envelope-paper'),
            ('Admitted', Applicant.Status.ADMITTED, 'bi-check-circle'),
        ]
        current = a.status
        stage_order = [s[1] for s in stages]
        try:
            idx = stage_order.index(current) if current in stage_order else -1
        except ValueError:
            idx = -1
        ctx['stages'] = [
            {
                'label': label, 'status': status, 'icon': icon,
                'done': (idx > i) if idx >= 0 else (current == Applicant.Status.ADMITTED),
                'active': (current == status) or (current == Applicant.Status.WAITLISTED and i == 0),
            }
            for i, (label, status, icon) in enumerate(stages)
        ]
        ctx['documents'] = a.documents.all()
        ctx['priorities'] = a.priority_flags.all()
        ctx['exam_assignments'] = a.exam_assignments.select_related('session').prefetch_related('marks')
        ctx['interview'] = getattr(a, 'interview', None)
        ctx['offer'] = getattr(a, 'offer', None)
        ctx['waitlist'] = getattr(a, 'waitlist_entry', None)
        ctx['can_offer'] = _can_offer(self.request.user)
        ctx['can_admit'] = _can_offer(self.request.user)
        return ctx


class ApplicantUploadDocumentView(LoginRequiredMixin, HasAnyGroupMixin, View):
    required_groups = OFFICE_GROUPS

    def post(self, request, pk):
        applicant = get_object_or_404(Applicant, pk=pk)
        form = DocumentAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.applicant = applicant
            doc.save()
            messages.success(request, 'Document uploaded.')
        else:
            messages.error(request, 'Could not upload document.')
        return redirect('admissions:applicant_detail', pk=pk)


class ApplicantAddPriorityView(LoginRequiredMixin, HasAnyGroupMixin, View):
    required_groups = OFFICE_GROUPS

    def post(self, request, pk):
        applicant = get_object_or_404(Applicant, pk=pk)
        form = PriorityFlagForm(request.POST)
        if form.is_valid():
            flag = form.save(commit=False)
            flag.applicant = applicant
            flag.verified_by = request.user
            flag.save()
            services.recompute_applicant_score(applicant)
            messages.success(request, 'Priority flag added.')
        else:
            messages.error(request, 'Could not add priority flag.')
        return redirect('admissions:applicant_detail', pk=pk)


# ── Exam (AD-16..AD-22) ─────────────────────────────────────────────
class ExamSessionListView(LoginRequiredMixin, HasAnyGroupMixin, ListView):
    model = EntranceExam
    template_name = 'admissions/exam_session_list.html'
    context_object_name = 'sessions'
    required_groups = OFFICE_GROUPS


class ExamSessionCreateView(LoginRequiredMixin, HasAnyGroupMixin, CreateView):
    model = EntranceExam
    form_class = EntranceExamForm
    template_name = 'admissions/exam_session_form.html'
    success_url = reverse_lazy('admissions:exam_session_list')
    required_groups = OFFICE_GROUPS

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ExamSessionDetailView(LoginRequiredMixin, HasAnyGroupMixin, DetailView):
    model = EntranceExam
    template_name = 'admissions/exam_session_detail.html'
    context_object_name = 'session'
    required_groups = OFFICE_GROUPS

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['assignments'] = self.object.assignments.select_related('applicant').prefetch_related('marks')
        ctx['assign_form'] = ExamAssignmentForm(session=self.object)
        ctx['subject_choices'] = ExamMark.Subject.choices
        return ctx


class AssignExamView(LoginRequiredMixin, HasAnyGroupMixin, View):
    required_groups = OFFICE_GROUPS

    def post(self, request, pk):
        session = get_object_or_404(EntranceExam, pk=pk)
        form = ExamAssignmentForm(request.POST, session=session)
        if form.is_valid():
            try:
                services.assign_applicant_to_session(
                    applicant=form.cleaned_data['applicant'], session=session,
                    seat_number=form.cleaned_data.get('seat_number') or None,
                )
                messages.success(request, 'Applicant assigned.')
            except ValidationError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'Could not assign applicant.')
        return redirect('admissions:exam_session_detail', pk=pk)


class RecordExamMarkView(LoginRequiredMixin, HasAnyGroupMixin, View):
    required_groups = OFFICE_GROUPS

    def post(self, request, assignment_id):
        assignment = get_object_or_404(ExamAssignment, pk=assignment_id)
        subject = request.POST.get('subject')
        score = request.POST.get('score')
        try:
            services.record_exam_mark(
                assignment=assignment, subject=subject, score=score,
            )
            messages.success(request, 'Mark saved.')
        except (ValidationError, ValueError) as e:
            messages.error(request, f'Could not save mark: {e}')
        return redirect('admissions:exam_session_detail', pk=assignment.session_id)


class PublishExamResultsView(LoginRequiredMixin, HasAnyGroupMixin, View):
    required_groups = HEAD_GROUPS

    def post(self, request, pk):
        session = get_object_or_404(EntranceExam, pk=pk)
        services.publish_exam_results(session)
        messages.success(request, f'Results published for {session.name}.')
        return redirect('admissions:exam_session_detail', pk=pk)


# ── Interview (AD-23..AD-26) ────────────────────────────────────────
class RecordInterviewView(LoginRequiredMixin, HasAnyGroupMixin, View):
    required_groups = OFFICE_GROUPS

    def get(self, request, pk):
        applicant = get_object_or_404(Applicant, pk=pk)
        existing = getattr(applicant, 'interview', None)
        form = InterviewForm(instance=existing)
        return render(request, 'admissions/interview_form.html', {
            'form': form, 'applicant': applicant,
        })

    def post(self, request, pk):
        applicant = get_object_or_404(Applicant, pk=pk)
        existing = getattr(applicant, 'interview', None)
        form = InterviewForm(request.POST, instance=existing)
        if form.is_valid():
            try:
                services.record_interview(
                    applicant=applicant,
                    interviewer=form.cleaned_data.get('interviewer') or request.user,
                    student_score=form.cleaned_data['student_score'],
                    parent_score=form.cleaned_data['parent_score'],
                    notes=form.cleaned_data.get('notes', ''),
                    recommendation=form.cleaned_data.get('recommendation', ''),
                    location=form.cleaned_data.get('location', ''),
                    conducted_at=form.cleaned_data.get('scheduled_for'),
                )
                messages.success(request, 'Interview recorded.')
                return redirect('admissions:applicant_detail', pk=pk)
            except ValidationError as e:
                messages.error(request, str(e))
        return render(request, 'admissions/interview_form.html', {
            'form': form, 'applicant': applicant,
        })


# ── Offer (AD-27..AD-34) ────────────────────────────────────────────
class IssueOfferView(LoginRequiredMixin, HasAnyGroupMixin, View):
    required_groups = HEAD_GROUPS

    def get(self, request, pk):
        applicant = get_object_or_404(Applicant, pk=pk)
        return render(request, 'admissions/offer_form.html', {
            'form': OfferIssueForm(), 'applicant': applicant,
        })

    def post(self, request, pk):
        applicant = get_object_or_404(Applicant, pk=pk)
        form = OfferIssueForm(request.POST)
        if form.is_valid():
            try:
                offer = services.issue_offer(
                    applicant=applicant, issued_by=request.user,
                    deadline_days=form.cleaned_data['deadline_days'],
                    notes=form.cleaned_data.get('notes', ''),
                )
                messages.success(request, f'Offer issued (deadline {offer.response_deadline}).')
                return redirect('admissions:applicant_detail', pk=pk)
            except ValidationError as e:
                messages.error(request, str(e))
        return render(request, 'admissions/offer_form.html', {
            'form': form, 'applicant': applicant,
        })


class AcceptOfferView(LoginRequiredMixin, HasAnyGroupMixin, View):
    required_groups = OFFICE_GROUPS

    def post(self, request, pk):
        offer = get_object_or_404(Offer, applicant_id=pk)
        try:
            offer.accept()
            messages.success(request, 'Offer accepted.')
        except ValidationError as e:
            messages.error(request, str(e))
        return redirect('admissions:applicant_detail', pk=pk)


class DeclineOfferView(LoginRequiredMixin, HasAnyGroupMixin, View):
    required_groups = OFFICE_GROUPS

    def post(self, request, pk):
        offer = get_object_or_404(Offer, applicant_id=pk)
        try:
            offer.decline(reason=request.POST.get('reason', ''))
            messages.success(request, 'Offer declined.')
        except ValidationError as e:
            messages.error(request, str(e))
        return redirect('admissions:applicant_detail', pk=pk)


# ── Admit (AD-40..AD-48) ────────────────────────────────────────────
class AdmitApplicantView(LoginRequiredMixin, HasAnyGroupMixin, View):
    required_groups = HEAD_GROUPS

    def get(self, request, pk):
        applicant = get_object_or_404(Applicant, pk=pk)
        return render(request, 'admissions/admit_confirm.html', {
            'form': AdmitForm(applicant=applicant), 'applicant': applicant,
        })

    def post(self, request, pk):
        applicant = get_object_or_404(Applicant, pk=pk)
        form = AdmitForm(request.POST, applicant=applicant)
        if form.is_valid():
            try:
                student = services.admit_applicant(
                    applicant=applicant,
                    admitted_by=request.user,
                    class_name=form.cleaned_data['class_name'],
                    stream=form.cleaned_data['stream'],
                    boarding_status=form.cleaned_data['boarding_status'],
                    hostel=form.cleaned_data.get('hostel', ''),
                    bed_number=form.cleaned_data.get('bed_number', ''),
                    reason=form.cleaned_data.get('reason', ''),
                )
                messages.success(
                    request,
                    f'Admitted as {student.student_id}. Invitations issued to the guardian.',
                )
                return redirect('students:detail', pk=student.pk)
            except ValidationError as e:
                messages.error(request, str(e))
        return render(request, 'admissions/admit_confirm.html', {
            'form': form, 'applicant': applicant,
        })


# ── Waitlist (AD-35..AD-39) ─────────────────────────────────────────
class WaitlistView(LoginRequiredMixin, HasAnyGroupMixin, ListView):
    model = WaitlistEntry
    template_name = 'admissions/waitlist_list.html'
    context_object_name = 'entries'
    required_groups = OFFICE_GROUPS

    def get_queryset(self):
        qs = WaitlistEntry.objects.select_related('applicant')
        cls = self.request.GET.get('class_name')
        if cls:
            qs = qs.filter(class_name=cls)
        return qs


class AddToWaitlistView(LoginRequiredMixin, HasAnyGroupMixin, View):
    required_groups = HEAD_GROUPS

    def post(self, request, pk):
        applicant = get_object_or_404(Applicant, pk=pk)
        class_name = request.POST.get('class_name') or applicant.applying_for
        stream = request.POST.get('stream', 'A')
        try:
            services.add_to_waitlist(
                applicant=applicant, class_name=class_name, stream=stream,
            )
            messages.success(request, 'Added to waitlist.')
        except ValidationError as e:
            messages.error(request, str(e))
        return redirect('admissions:applicant_detail', pk=pk)