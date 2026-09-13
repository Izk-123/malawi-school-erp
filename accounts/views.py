from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView, PasswordChangeView as BasePasswordChangeView,
    PasswordResetView as BasePasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView as BasePasswordResetConfirmView, PasswordResetCompleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, ListView, DetailView, View

from students.models import Student
from teachers.models import Teacher
from attendance.models import AttendanceRecord
from fees.models import FeeTransaction
from grades.models import GradeRecord
from staff.models import StaffMember
from timetable.models import TimetablePeriod
from attendance.services import todays_school_wide_percentage
from notifications.tasks import send_account_event_notification

from .mixins import RoleRequiredMixin
from .models import User, AuditLog
from .forms import RoleAwareLoginForm, SelfRegistrationForm, UserCreateForm, UserUpdateForm, ProfileForm
from .signals import record_password_history


class SchoolLoginView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = RoleAwareLoginForm
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
            'todays_attendance_percentage': todays_school_wide_percentage(),  # AT-13
        })
        template = 'dashboard/admin_dashboard.html'

    elif role == 'teacher':
        teacher = Teacher.objects.filter(user=user).first()
        classes = teacher.classes_taught_list() if teacher else []
        context.update({
            'teacher': teacher,
            'classes': classes,
            'today_periods': TimetablePeriod.objects.filter(teacher=teacher, day='Monday') if teacher else [],
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
        context.update({
            'staff_count': StaffMember.objects.count(),
            'active_teachers': Teacher.objects.filter(status='active').count(),
            'staff_list': StaffMember.objects.all(),
        })
        template = 'dashboard/staff_dashboard.html'

    return render(request, template, context)


# --------------------------------------------------------------------------
# AC-02/03/04: self-registration for Students/Parents
# --------------------------------------------------------------------------
class SignUpView(CreateView):
    model = User
    form_class = SelfRegistrationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('accounts:login')

    def dispatch(self, request, *args, **kwargs):
        from django.conf import settings
        if not getattr(settings, 'ENABLE_SELF_REGISTRATION', True):
            messages.error(request, 'Self-registration is currently disabled. Please contact your school administrator.')
            return redirect('accounts:login')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        record_password_history(self.object, form.cleaned_data['password1'])
        AuditLog.objects.create(user=self.object, action=AuditLog.Action.ACCOUNT_CREATED,
                                 username_attempted=self.object.username, detail='Self-registered')
        messages.success(self.request, 'Account created! You can now log in.')
        return response


# --------------------------------------------------------------------------
# AC-11/12/14: password change & reset (Django's built-in views, styled)
# --------------------------------------------------------------------------
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
        AuditLog.objects.create(user=form.user, action=AuditLog.Action.PASSWORD_RESET, username_attempted=form.user.username)
        return response


class SchoolPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'


# --------------------------------------------------------------------------
# AC-20/21: self-service profile management
# --------------------------------------------------------------------------
class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated.')
        return super().form_valid(form)


# --------------------------------------------------------------------------
# AC-01/22/24/26/27: admin user management
# --------------------------------------------------------------------------
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
            from axes.utils import get_client_ip_address  # noqa
            from axes.models import AccessAttempt
            ctx['is_locked'] = AccessAttempt.objects.filter(username=self.object.username, failures_since_start__gte=5).exists()
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

    def form_valid(self, form):
        response = super().form_valid(form)
        record_password_history(self.object, form.cleaned_data['password1'])
        AuditLog.objects.create(user=self.object, action=AuditLog.Action.ACCOUNT_CREATED,
                                 username_attempted=self.object.username, detail=f'Created by {self.request.user}')
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
        action = AuditLog.Action.ACCOUNT_ACTIVATED if target.is_active else AuditLog.Action.ACCOUNT_DEACTIVATED
        AuditLog.objects.create(user=target, action=action, username_attempted=target.username,
                                 detail=f'Toggled by {request.user}')
        send_account_event_notification.delay(target.id, 'activated' if target.is_active else 'deactivated')
        messages.success(request, f'{target.username} is now {"active" if target.is_active else "inactive"}.')
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
        AuditLog.objects.create(user=target, action=AuditLog.Action.ACCOUNT_UNLOCKED,
                                 username_attempted=target.username, detail=f'Unlocked by {request.user}')
        messages.success(request, f'{target.username} has been unlocked.')
        return redirect('accounts:user_detail', pk=pk)
