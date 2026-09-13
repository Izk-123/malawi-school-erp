import csv
import datetime

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView

from accounts.mixins import RoleRequiredMixin
from students.models import Student
from teachers.models import Teacher
from notifications.tasks import notify_low_attendance, notify_absence

from .models import AttendanceRecord, is_school_day
from .filters import AttendanceFilter
from .resources import AttendanceResource
from . import services


def _teacher_classes(user):
    """AT-01: the (class_name, stream) pairs a teacher is actually assigned to."""
    teacher = Teacher.objects.filter(user=user).first()
    if not teacher:
        return []
    return list(teacher.assignments.values_list('class_name', 'stream').distinct())


class MarkAttendanceView(LoginRequiredMixin, RoleRequiredMixin, View):
    """AT-01/02/03/05/14/15/16: shows the roster for a class/date and saves marks."""
    allowed_roles = ['admin', 'teacher']

    def _class_choices(self, request):
        if request.user.role == 'teacher' and not request.user.is_superuser:
            pairs = _teacher_classes(request.user)
            return pairs if pairs else Student.objects.values_list('class_name', 'stream').distinct()[:0]
        return Student.objects.values_list('class_name', 'stream').distinct()

    def get(self, request):
        class_choices = list(self._class_choices(request))
        default_class, default_stream = (class_choices[0] if class_choices else ('Form 3', 'A'))
        class_name = request.GET.get('class_name', default_class)
        stream = request.GET.get('stream', default_stream)
        date_str = request.GET.get('date') or datetime.date.today().isoformat()
        date = datetime.date.fromisoformat(date_str)

        # AT-01: a teacher can only mark a class they're actually assigned to.
        if request.user.role == 'teacher' and not request.user.is_superuser:
            if (class_name, stream) not in class_choices:
                messages.error(request, "You aren't assigned to that class.")
                return redirect('teachers:my_classes')

        students = services.get_roster(class_name, stream)
        existing = {
            r.student_id: r.status for r in AttendanceRecord.objects.filter(
                student__in=students, date=date, period=''
            )
        }
        context = {
            'students': students,
            'existing': existing,
            'class_name': class_name,
            'stream': stream,
            'date': date.isoformat(),
            'classes': class_choices,
            'is_school_day': is_school_day(date),
            'is_future': date > datetime.date.today(),
            'edit_window_hours': settings.ATTENDANCE_EDIT_WINDOW_HOURS,
        }
        return render(request, 'attendance/mark_attendance.html', context)

    def post(self, request):
        class_name = request.POST.get('class_name')
        stream = request.POST.get('stream')
        date_str = request.POST.get('date')
        date = datetime.date.fromisoformat(date_str)
        marks = {
            int(key.replace('status_', '')): status
            for key, status in request.POST.items() if key.startswith('status_')
        }

        try:
            touched_ids, skipped_ids = services.save_bulk_attendance(class_name, stream, date, marks, request.user)
        except ValidationError as e:
            messages.error(request, str(e.message) if hasattr(e, 'message') else str(e))
            return redirect(f"{reverse('attendance:mark')}?class_name={class_name}&stream={stream}&date={date_str}")

        # AT-18/19: notify parents on absence, and flag anyone below the
        # configurable low-attendance threshold.
        for record in AttendanceRecord.objects.filter(id__in=touched_ids).select_related('student'):
            if record.status == AttendanceRecord.Status.ABSENT:
                notify_absence.delay(record.student_id, str(record.date))
            if record.student.attendance_percentage < settings.ATTENDANCE_LOW_THRESHOLD:
                notify_low_attendance.delay(record.student_id)

        request.session['attendance_last_batch'] = touched_ids
        msg = f'Attendance saved for {len(touched_ids)} students on {date_str}.'
        if skipped_ids:
            msg += f' {len(skipped_ids)} record(s) were outside the edit window and were not changed.'
        messages.success(request, msg)
        return redirect(f"{reverse('attendance:mark')}?class_name={class_name}&stream={stream}&date={date_str}")


class MarkAllPresentView(LoginRequiredMixin, RoleRequiredMixin, View):
    """AT-03/AT-24: one-click bulk action, then teachers just fix exceptions."""
    allowed_roles = ['admin', 'teacher']

    def post(self, request):
        class_name = request.POST.get('class_name')
        stream = request.POST.get('stream')
        date_str = request.POST.get('date')
        date = datetime.date.fromisoformat(date_str)
        try:
            count = services.mark_all_present(class_name, stream, date, request.user)
            messages.success(request, f'Marked {count} students present. Adjust any exceptions below.')
        except ValidationError as e:
            messages.error(request, str(e))
        return redirect(f"{reverse('attendance:mark')}?class_name={class_name}&stream={stream}&date={date_str}")


class UndoLastMarkView(LoginRequiredMixin, RoleRequiredMixin, View):
    """Usability NFR: undo the most recent attendance save in this session."""
    allowed_roles = ['admin', 'teacher']

    def post(self, request):
        record_ids = request.session.pop('attendance_last_batch', [])
        if not record_ids:
            messages.warning(request, 'Nothing to undo.')
        else:
            reverted, deleted = services.undo_records(record_ids, request.user)
            messages.success(request, f'Undo complete: {reverted} reverted, {deleted} removed.')
        return redirect(request.POST.get('next') or reverse('attendance:mark'))


class TeacherAttendanceHistoryView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    """AT-09: a teacher's attendance history for their own classes, by date range."""
    model = AttendanceRecord
    template_name = 'attendance/history.html'
    context_object_name = 'records'
    paginate_by = 30
    allowed_roles = ['teacher']

    def get_queryset(self):
        pairs = _teacher_classes(self.request.user)
        qs = AttendanceRecord.objects.select_related('student')
        if pairs:
            from django.db.models import Q
            q = Q()
            for cls, stream in pairs:
                q |= Q(class_name_at_time=cls, stream_at_time=stream)
            qs = qs.filter(q)
        else:
            qs = qs.none()
        self.filterset = AttendanceFilter(self.request.GET, queryset=qs)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter'] = self.filterset
        ctx['stats'] = services.compute_stats(self.get_queryset())
        return ctx


class AdminAttendanceSummaryView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    """AT-08: daily/range summary for any class or the whole school."""
    model = AttendanceRecord
    template_name = 'attendance/admin_summary.html'
    context_object_name = 'records'
    paginate_by = 30
    allowed_roles = ['admin']

    def get_queryset(self):
        qs = AttendanceRecord.objects.select_related('student')
        self.filterset = AttendanceFilter(self.request.GET, queryset=qs)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter'] = self.filterset
        ctx['stats'] = services.compute_stats(self.get_queryset())
        ctx['todays_percentage'] = services.todays_school_wide_percentage()
        ctx['classes'] = Student.objects.values_list('class_name', 'stream').distinct()
        return ctx


class AttendanceExportView(LoginRequiredMixin, RoleRequiredMixin, View):
    """AT-11/AT-25: export the (filtered) attendance data to CSV."""
    allowed_roles = ['admin', 'teacher']

    def get(self, request):
        qs = AttendanceRecord.objects.select_related('student')
        if request.user.role == 'teacher' and not request.user.is_superuser:
            pairs = _teacher_classes(request.user)
            from django.db.models import Q
            q = Q()
            for cls, stream in pairs:
                q |= Q(class_name_at_time=cls, stream_at_time=stream)
            qs = qs.filter(q) if pairs else qs.none()
        qs = AttendanceFilter(request.GET, queryset=qs).qs
        dataset = AttendanceResource().export(qs)
        response = HttpResponse(dataset.csv, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="attendance_export.csv"'
        return response


class MyAttendanceView(LoginRequiredMixin, RoleRequiredMixin, View):
    """AT-10: a student's own attendance history + percentage."""
    allowed_roles = ['student']

    def get(self, request):
        student = Student.objects.filter(user=request.user).first()
        records = AttendanceRecord.objects.filter(student=student) if student else AttendanceRecord.objects.none()
        return render(request, 'attendance/my_attendance.html', {
            'student': student, 'records': records[:60], 'stats': services.compute_stats(records),
        })


class ChildAttendanceView(LoginRequiredMixin, RoleRequiredMixin, View):
    """AT-10: a parent's view of a child's attendance history + percentage."""
    allowed_roles = ['parent']

    def get(self, request, pk):
        student = Student.objects.filter(pk=pk, guardians=request.user).first()
        if not student:
            messages.error(request, "That student isn't linked to your account.")
            return redirect('students:my_children')
        records = AttendanceRecord.objects.filter(student=student)
        return render(request, 'attendance/my_attendance.html', {
            'student': student, 'records': records[:60], 'stats': services.compute_stats(records),
        })


class AttendanceSummaryView(LoginRequiredMixin, RoleRequiredMixin, View):
    """Legacy simple summary (kept for the sidebar link); parents/teachers
    land here and get routed to the richer views above."""
    allowed_roles = ['admin', 'teacher', 'parent']

    def get(self, request):
        if request.user.role == 'parent':
            students = Student.objects.filter(guardians=request.user)
        else:
            students = Student.objects.all()
        return render(request, 'attendance/summary.html', {'students': students})
