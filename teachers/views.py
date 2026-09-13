from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from accounts.mixins import RoleRequiredMixin
from students.models import Student
from timetable.models import TimetablePeriod
from .models import Teacher
from .forms import TeacherForm, TeacherSelfServiceForm
from .filters import TeacherFilter


class TeacherListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = Teacher
    template_name = 'teachers/teacher_list.html'
    context_object_name = 'teachers'
    paginate_by = 20  # TC-22
    allowed_roles = ['admin']

    def get_queryset(self):
        self.filterset = TeacherFilter(self.request.GET, queryset=super().get_queryset())
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter'] = self.filterset
        return ctx


class TeacherDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    model = Teacher
    template_name = 'teachers/teacher_detail.html'
    context_object_name = 'teacher'
    allowed_roles = ['admin']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # TC-18: teaching schedule for the current term.
        ctx['schedule'] = TimetablePeriod.objects.filter(teacher=self.object)
        return ctx


class TeacherCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = Teacher
    form_class = TeacherForm
    template_name = 'teachers/teacher_form.html'
    success_url = reverse_lazy('teachers:list')
    allowed_roles = ['admin']

    def form_valid(self, form):
        messages.success(self.request, f'Teacher {form.instance.full_name} added.')
        return super().form_valid(form)


class TeacherUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = Teacher
    form_class = TeacherForm
    template_name = 'teachers/teacher_form.html'
    success_url = reverse_lazy('teachers:list')
    allowed_roles = ['admin']

    def form_valid(self, form):
        messages.success(self.request, f'Teacher {form.instance.full_name} updated.')
        return super().form_valid(form)


class MyClassesView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    """Teacher portal: classes + student counts for the logged-in teacher."""
    template_name = 'teachers/my_classes.html'
    context_object_name = 'assignments'
    allowed_roles = ['teacher']

    def get_queryset(self):
        teacher = Teacher.objects.filter(user=self.request.user).first()
        self.teacher = teacher
        if not teacher:
            return []
        return teacher.assignments.all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        for assignment in ctx['assignments']:
            assignment.student_count = Student.objects.filter(
                class_name=assignment.class_name, stream=assignment.stream
            ).count()
        ctx['teacher'] = self.teacher
        return ctx


class ClassRosterView(LoginRequiredMixin, RoleRequiredMixin, View):
    """TC-33: a teacher's list of students in one of their classes, with
    guardian contact details."""
    allowed_roles = ['teacher', 'admin']

    def get(self, request, class_name, stream):
        teacher = Teacher.objects.filter(user=request.user).first()
        if request.user.role == 'teacher' and teacher:
            allowed = teacher.assignments.filter(class_name=class_name, stream=stream).exists()
            if not allowed and not request.user.is_superuser:
                messages.error(request, "You aren't assigned to that class.")
                return redirect('teachers:my_classes')
        students = Student.objects.filter(class_name=class_name, stream=stream)
        return render(request, 'teachers/class_roster.html', {
            'students': students, 'class_name': class_name, 'stream': stream,
        })


class TeacherProfileView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    """TC-30/31: a teacher viewing/editing their own limited profile fields."""
    model = Teacher
    form_class = TeacherSelfServiceForm
    template_name = 'teachers/my_profile.html'
    success_url = reverse_lazy('teachers:my_profile')
    allowed_roles = ['teacher']

    def get_object(self, queryset=None):
        return get_object_or_404(Teacher, user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated.')
        return super().form_valid(form)
