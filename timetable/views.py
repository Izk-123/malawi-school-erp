from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView

from accounts.mixins import RoleRequiredMixin
from students.models import Student
from .models import TimetablePeriod


class TimetableListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = TimetablePeriod
    template_name = 'timetable/timetable.html'
    context_object_name = 'periods'
    allowed_roles = ['admin', 'teacher']

    def get_queryset(self):
        class_name = self.request.GET.get('class_name', 'Form 3')
        stream = self.request.GET.get('stream', 'A')
        self.class_name, self.stream = class_name, stream
        return TimetablePeriod.objects.filter(class_name=class_name, stream=stream)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['classes'] = Student.objects.values_list('class_name', 'stream').distinct()
        ctx['class_name'] = self.class_name
        ctx['stream'] = self.stream
        ctx['days'] = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        return ctx


class MyTimetableView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ['student']

    def get(self, request):
        student = Student.objects.filter(user=request.user).first()
        periods = TimetablePeriod.objects.filter(
            class_name=student.class_name, stream=student.stream
        ) if student else []
        return render(request, 'timetable/my_timetable.html', {
            'student': student, 'periods': periods,
            'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
        })
