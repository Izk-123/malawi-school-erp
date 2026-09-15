"""
Accounts app views.

Covers:
  - Login / logout / dashboard (role-based landing)
  - Self-registration (Student/Parent) with email + phone verification kickoff
  - Email verification (token-based) and phone verification (OTP)
  - Password change & reset (Django built-ins, styled)
  - Self-service profile (read + edit, inline avatar actions, live email check)
  - Admin user management (list, detail, create, update, activate, unlock)
"""
import random
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    PasswordChangeView as BasePasswordChangeView,
    PasswordResetView as BasePasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView as BasePasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DetailView, View

# Cross-app imports
from students.models import Student
from teachers.models import Teacher
from attendance.models import AttendanceRecord  # noqa: F401  (parity with original)
from fees.models import FeeTransaction  # noqa: F401
from grades.models import GradeRecord
from staff.models import StaffMember
from timetable.models import TimetablePeriod
from attendance.services import todays_school_wide_percentage
from notifications.tasks import send_account_event_notification

from .mixins import RoleRequiredMixin
from .models import (
    User,
    AuditLog,
    EmailVerificationToken,
    PhoneOTP,
)
from .forms import (
    SchoolLoginForm,
    SelfRegistrationForm,
    UserCreateForm,
    UserUpdateForm,
    ProfileForm,
)
from .signals import record_password_history


# ---------------------------------------------------------------------------
# Role metadata for the profile page
# ---------------------------------------------------------------------------
ROLE_META = {
    'admin':   {'icon': 'bi-shield-fill-check',
                'description': 'Full system access, user management, reporting'},
    'teacher': {'icon': 'bi-person-video3',
                'description': 'Classes, attendance, grade entry, syllabus'},
    'student': {'icon': 'bi-mortarboard',
                'description': 'Attendance, grades, fees, timetable'},
    'parent':  {'icon': 'bi-people',
                'description': 'Children, fees, attendance, messages'},
    'staff':   {'icon': 'bi-person-badge',
                'description': 'Non-teaching roles, leave, tickets, library'},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _normalise_malawi_phone(raw: str) -> str:
    """Turn '991234567' or '+265 991 234 567' into '+265991234567'."""
    digits = ''.join(c for c in (raw or '') if c.isdigit())
    if digits.startswith('265'):
        digits = digits[3:]
    digits = digits[-9:]
    return f'+265{digits}' if len(digits) == 9 else ''


def _send_verification_email(request, user):
    """Issue a fresh EmailVerificationToken and email the verify URL."""
    EmailVerificationToken.objects.filter(user=user, used=False).update(used=True)
    token = EmailVerificationToken.objects.create(user=user)
    verify_url = request.build_absolute_uri(
        reverse('accounts:verify_email', kwargs={'token': token.token})
    )
    send_mail(
        'Malawi School ERP — verify your email',
        (
            f'Hello {user.get_full_name() or user.username},\n\n'
            f'Please click the link below to verify your email address '
            f'(valid for 24 hours):\n\n{verify_url}\n\n'
            f"If you didn't create this account, you can ignore this email."
        ),
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    )
    return token


def _send_phone_otp(user, phone):
    """Issue a fresh PhoneOTP for `phone` and dispatch it via SMS."""
    PhoneOTP.objects.filter(user=user, used=False).update(used=True)
    code = f'{random.randint(0, 999999):06d}'
    PhoneOTP.objects.create(user=user, phone_number=phone, otp_code=code)
    try:
        from notifications.tasks import send_sms
        send_sms.delay(
            phone,
            f'Your Malawi School ERP verification code is {code}. '
            f'It expires in 10 minutes.',
        )
    except Exception:
        # Never let a delivery failure break the flow.
        pass
    return code


def _profile_stats(user, role):
    """Return the quick-stat strip for the profile page, per role."""
    try:
        if role == 'teacher':
            t = Teacher.objects.filter(user=user).first()
            if t:
                return [
                    {'value': len(t.classes_taught_list() or []), 'label': 'Classes'},
                    {'value': getattr(t, 'students_count', '—'), 'label': 'Students'},
                    {'value': getattr(t, 'years_of_service', '—'), 'label': 'Years'},
                ]
        elif role == 'student':
            s = Student.objects.filter(user=user).first()
            if s:
                return [
                    {'value': f"{s.attendance_percentage}%", 'label': 'Attendance'},
                    {'value': s.average_grade, 'label': 'Average'},
                    {'value': f"Form {getattr(s, 'form', '—')}", 'label': 'Class'},
                ]
        elif role == 'parent':
            children = Student.objects.filter(guardians=user)
            total = sum(c.balance for c in children)
            avg = (
                round(sum(c.attendance_percentage for c in children) / children.count(), 1)
                if children.count() else 0
            )
            return [
                {'value': children.count(), 'label': 'Children'},
                {'value': f"MK {total:,.0f}", 'label': 'Balance'},
                {'value': f"{avg}%", 'label': 'Attendance'},
            ]
    except Exception:
        # Never let a stats failure break the profile page.
        pass
    return []


# ---------------------------------------------------------------------------
# Login / logout / dashboard
# ---------------------------------------------------------------------------
class SchoolLoginView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = SchoolLoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('accounts:dashboard')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
def dashboard(request):
    user = request.user
    role = 'admin' if user.is_superuser else user.role
    context = {'role': role}

    if role == 'admin':
        students = Student.objects.all()
        context.update({
            'total_students': students.count(),
            'active_students': students.filter(status='active').count(),
            'total_teachers': Teacher.objects.count(),
            'active_teachers': Teacher.objects.filter(status='active').count(),
            'total_staff': StaffMember.objects.count(),
            'fees_expected': sum(s.fees_total for s in students) or 0,
            'fees_collected': sum(s.fees_paid for s in students) or 0,
            'avg_attendance': round(
                sum(s.attendance_percentage for s in students) / students.count(), 1
            ) if students.count() else 0,
            'recent_students': students.order_by('-id')[:5],
            'today_periods': TimetablePeriod.objects.filter(day='Monday')[:5],
            'todays_attendance_percentage': todays_school_wide_percentage(),
        })
        template = 'dashboard/admin_dashboard.html'

    elif role == 'teacher':
        teacher = Teacher.objects.filter(user=user).first()
        classes = teacher.classes_taught_list() if teacher else []
        context.update({
            'teacher': teacher,
            'classes': classes,
            'today_periods': (
                TimetablePeriod.objects.filter(teacher=teacher, day='Monday')
                if teacher else []
            ),
        })
        template = 'dashboard/teacher_dashboard.html'

    elif role == 'student':
        student = Student.objects.filter(user=user).first()
        context.update({
            'student': student,
            'grades': GradeRecord.objects.filter(student=student)[:10] if student else [],
        })
        template = 'dashboard/student_dashboard.html'

    elif role == 'parent':
        children = Student.objects.filter(guardians=user)
        context.update({
            'children': children,
            'total_balance': sum(c.balance for c in children),
            'avg_attendance': round(
                sum(c.attendance_percentage for c in children) / children.count(), 1
            ) if children.count() else 0,
        })
        template = 'dashboard/parent_dashboard.html'

    else:  # staff
        return redirect('staff:dashboard')

    return render(request, template, context)


# ---------------------------------------------------------------------------
# AC-02/03/04: self-registration for Students/Parents
# ---------------------------------------------------------------------------
class SignUpView(CreateView):
    model = User
    form_class = SelfRegistrationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('accounts:verify_email_pending')

    def dispatch(self, request, *args, **kwargs):
        if not getattr(settings, 'ENABLE_SELF_REGISTRATION', True):
            messages.error(
                request,
                'Self-registration is currently disabled. '
                'Please contact your school administrator.',
            )
            return redirect('accounts:login')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)

        # New self-registered accounts start unverified on both channels.
        self.object.email_verified = False
        self.object.phone_verified = False
        self.object.save(update_fields=['email_verified', 'phone_verified'])

        record_password_history(self.object, form.cleaned_data['password1'])

        AuditLog.objects.create(
            user=self.object,
            action=AuditLog.Action.ACCOUNT_CREATED,
            username_attempted=self.object.username,
            ip_address=_client_ip(self.request),
            detail='Self-registered',
        )

        # Fire the verification email and, if a phone was given, the SMS OTP.
        try:
            _send_verification_email(self.request, self.object)
        except Exception:
            pass
        if self.object.phone_number:
            try:
                _send_phone_otp(self.object, self.object.phone_number)
            except Exception:
                pass

        # Log the new user in so they can proceed to the pending screen.
        auth_login(self.request, self.object)

        messages.success(
            self.request,
            'Account created! Check your email to verify your address.',
        )
        return response


# ---------------------------------------------------------------------------
# AC-07c/e: email verification
# ---------------------------------------------------------------------------
@login_required
def verify_email_pending(request):
    """'Check your inbox' page."""
    if request.user.email_verified:
        return redirect('accounts:dashboard')
    return render(request, 'registration/verify_email_pending.html')


@login_required
def resend_email(request):
    """POST — issue a fresh verification email."""
    if request.method != 'POST':
        return redirect('accounts:verify_email_pending')

    _send_verification_email(request, request.user)
    messages.success(
        request,
        "If that email is on file, we've sent a new verification link.",
    )
    return redirect('accounts:verify_email_pending')


def verify_email(request, token):
    """GET — one-click verification handler reached from the emailed link."""
    record = (
        EmailVerificationToken.objects
        .filter(token=token)
        .select_related('user')
        .first()
    )
    if not record or not record.is_valid():
        messages.error(request, 'This verification link is invalid or has expired.')
        return redirect('accounts:login')

    record.used = True
    record.save(update_fields=['used'])

    user = record.user
    user.email_verified = True
    user.save(update_fields=['email_verified'])

    AuditLog.objects.create(
        user=user,
        action=AuditLog.Action.ACCOUNT_ACTIVATED,
        username_attempted=user.username,
        ip_address=_client_ip(request),
        detail='Email verified',
    )
    messages.success(request, 'Your email is verified.')

    if request.user.is_authenticated:
        return render(request, 'registration/verify_email_success.html')
    return redirect('accounts:login')


# ---------------------------------------------------------------------------
# AC-07c/e: phone verification
# ---------------------------------------------------------------------------
@login_required
def phone_request(request):
    """GET shows the form; POST issues a new 6-digit OTP via SMS."""
    user = request.user
    prefill = (user.phone_number or '').replace('+265', '')

    if user.phone_verified:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        raw = request.POST.get('phone', '')
        phone = _normalise_malawi_phone(raw)
        if not phone:
            return render(request, 'registration/phone_request.html', {
                'error': 'Please enter a valid Malawian mobile number (9 digits).',
                'prefill_phone': raw,
            })

        _send_phone_otp(user, phone)
        messages.info(request, f'We sent a 6-digit code to {phone}.')
        return redirect('accounts:phone_confirm')

    return render(request, 'registration/phone_request.html', {
        'prefill_phone': prefill,
    })


@login_required
def phone_confirm(request):
    """GET shows the OTP screen; POST validates the submitted 6-digit code."""
    user = request.user

    if user.phone_verified:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        code = (request.POST.get('otp_code') or '').strip()
        phone = request.POST.get('phone', '') or (user.phone_number or '')

        otp = (
            PhoneOTP.objects
            .filter(user=user, phone_number=phone, used=False)
            .order_by('-created_at')
            .first()
        )

        if not otp or not otp.is_valid():
            return render(request, 'registration/phone_confirm.html', {
                'phone_number': phone,
                'error': 'That code has expired. Please request a new one.',
            })

        if otp.otp_code != code:
            otp.attempts += 1
            otp.save(update_fields=['attempts'])
            return render(request, 'registration/phone_confirm.html', {
                'phone_number': phone,
                'error': 'Incorrect code. Please try again.',
            })

        otp.used = True
        otp.save(update_fields=['used'])

        user.phone_verified = True
        user.phone_number = phone
        user.save(update_fields=['phone_verified', 'phone_number'])

        AuditLog.objects.create(
            user=user,
            action=AuditLog.Action.ACCOUNT_ACTIVATED,
            username_attempted=user.username,
            ip_address=_client_ip(request),
            detail='Phone verified',
        )

        messages.success(request, 'Phone verified. Welcome aboard!')
        return redirect('accounts:dashboard')

    latest = (
        PhoneOTP.objects
        .filter(user=user, used=False)
        .order_by('-created_at')
        .first()
    )
    if not latest:
        return redirect('accounts:phone_request')

    return render(request, 'registration/phone_confirm.html', {
        'phone_number': latest.phone_number,
    })


# ---------------------------------------------------------------------------
# AC-11/12/14: password change & reset
# ---------------------------------------------------------------------------
class PasswordChangeView(LoginRequiredMixin, BasePasswordChangeView):
    template_name = 'registration/password_change_form.html'
    success_url = reverse_lazy('accounts:password_change_done')

    def form_valid(self, form):
        response = super().form_valid(form)
        record_password_history(self.request.user, form.cleaned_data['new_password1'])
        return response


class PasswordChangeDoneView(LoginRequiredMixin, View):
    def get(self, request):
        messages.success(request, 'Your password has been changed.')
        return redirect('accounts:profile')


class PasswordResetView(BasePasswordResetView):
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')


class SchoolPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'


class SchoolPasswordResetConfirmView(BasePasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')

    def form_valid(self, form):
        response = super().form_valid(form)
        record_password_history(form.user, form.cleaned_data['new_password1'])
        AuditLog.objects.create(
            user=form.user,
            action=AuditLog.Action.PASSWORD_RESET,
            username_attempted=form.user.username,
            ip_address=_client_ip(self.request),
        )
        return response


class SchoolPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'


# ---------------------------------------------------------------------------
# AC-20/21: self-service profile (read + edit, inline avatar actions)
# ---------------------------------------------------------------------------
class ProfileView(LoginRequiredMixin, UpdateView):
    """
    Read-first profile page. Also accepts lightweight POST actions for the
    avatar directly from the read view, so a user can change their picture
    without switching to edit mode.
    """
    model = User
    form_class = ProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        role = 'admin' if user.is_superuser else user.role
        ctx['role_meta'] = ROLE_META.get(role, ROLE_META['student'])
        ctx['stats'] = _profile_stats(user, role)
        return ctx

    def post(self, request, *args, **kwargs):
        # Remove current picture
        if request.POST.get('remove_picture') == '1':
            if request.user.profile_picture:
                request.user.profile_picture.delete(save=False)
                request.user.profile_picture = None
                request.user.save(update_fields=['profile_picture'])
            messages.success(request, 'Profile photo removed.')
            return redirect('accounts:profile')

        # Upload a new picture directly from the read view
        picture = request.FILES.get('profile_picture')
        if picture is not None:
            request.user.profile_picture = picture
            request.user.save(update_fields=['profile_picture'])
            messages.success(request, 'Profile photo updated.')
            return redirect('accounts:profile')

        # Placeholder for delete-account confirmation
        if request.POST.get('delete') == '1':
            messages.error(
                request,
                'Account deletion must be confirmed by a school administrator. '
                'Please contact the office.',
            )
            return redirect('accounts:profile')

        # Anything else → fall through to the UpdateView path
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated.')
        return super().form_valid(form)


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Full-page edit form for the current user."""
    model = User
    form_class = ProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        role = 'admin' if user.is_superuser else user.role
        ctx['role_meta'] = ROLE_META.get(role, ROLE_META['student'])
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated.')
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Live-validation endpoint for the profile edit form
# ---------------------------------------------------------------------------
@login_required
def check_email(request):
    """
    GET ?email=<value>
    Returns {"available": true} if the email is free, or
    {"available": false, "error": "..."} with a human message.
    Used by the profile-edit form's debounced async check.
    """
    email = (request.GET.get('email') or '').strip().lower()
    if not email:
        return JsonResponse(
            {'available': False, 'error': 'Email is required.'},
            status=400,
        )

    # Cheap format guard before hitting the DB
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}$', email):
        return JsonResponse(
            {'available': False, 'error': 'Enter a valid email address.'},
        )

    taken = (
        User.objects
        .filter(email__iexact=email)
        .exclude(pk=request.user.pk)
        .exists()
    )
    if taken:
        return JsonResponse(
            {'available': False, 'error': 'This email is already in use.'},
        )
    return JsonResponse({'available': True})


# ---------------------------------------------------------------------------
# AC-01/22/24/26/27: admin user management
# ---------------------------------------------------------------------------
class UserListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 25
    allowed_roles = ['admin']

    def get_queryset(self):
        qs = super().get_queryset().order_by('role', 'username')
        role = self.request.GET.get('role')
        if role:
            qs = qs.filter(role=role)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(username__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['roles'] = User.Role.choices
        return ctx


class UserDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'account'
    allowed_roles = ['admin']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['audit_logs'] = AuditLog.objects.filter(user=self.object)[:20]
        try:
            from axes.models import AccessAttempt
            ctx['is_locked'] = AccessAttempt.objects.filter(
                username=self.object.username,
                failures_since_start__gte=5,
            ).exists()
        except Exception:
            ctx['is_locked'] = False
        return ctx


class UserCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    """AC-01: admin creates accounts for any role."""
    model = User
    form_class = UserCreateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')
    allowed_roles = ['admin']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['object'] = None
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        record_password_history(self.object, form.cleaned_data['password1'])
        AuditLog.objects.create(
            user=self.object,
            action=AuditLog.Action.ACCOUNT_CREATED,
            username_attempted=self.object.username,
            ip_address=_client_ip(self.request),
            detail=f'Created by {self.request.user}',
        )
        messages.success(self.request, f'Account "{self.object.username}" created.')
        return response


class UserUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')
    allowed_roles = ['admin']

    def form_valid(self, form):
        messages.success(self.request, f'Account "{self.object.username}" updated.')
        return super().form_valid(form)


class UserToggleActiveView(LoginRequiredMixin, RoleRequiredMixin, View):
    """AC-24: activate/deactivate/suspend accounts."""
    allowed_roles = ['admin']

    def post(self, request, pk):
        target = get_object_or_404(User, pk=pk)
        target.is_active = not target.is_active
        target.save(update_fields=['is_active'])

        action = (
            AuditLog.Action.ACCOUNT_ACTIVATED
            if target.is_active else AuditLog.Action.ACCOUNT_DEACTIVATED
        )
        AuditLog.objects.create(
            user=target,
            action=action,
            username_attempted=target.username,
            ip_address=_client_ip(request),
            detail=f'Toggled by {request.user}',
        )

        send_account_event_notification.delay(
            target.id,
            'activated' if target.is_active else 'deactivated',
        )

        messages.success(
            request,
            f'{target.username} is now '
            f'{"active" if target.is_active else "inactive"}.',
        )
        return redirect('accounts:user_detail', pk=pk)


class UserUnlockView(LoginRequiredMixin, RoleRequiredMixin, View):
    """AC-26: admin manually unlocks an account locked by django-axes."""
    allowed_roles = ['admin']

    def post(self, request, pk):
        target = get_object_or_404(User, pk=pk)
        try:
            from axes.utils import reset
            reset(username=target.username)
        except Exception:
            pass

        AuditLog.objects.create(
            user=target,
            action=AuditLog.Action.ACCOUNT_UNLOCKED,
            username_attempted=target.username,
            ip_address=_client_ip(request),
            detail=f'Unlocked by {request.user}',
        )
        messages.success(request, f'{target.username} has been unlocked.')
        return redirect('accounts:user_detail', pk=pk)