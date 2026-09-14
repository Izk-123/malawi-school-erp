from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from accounts.mixins import RoleRequiredMixin
from teachers.models import Teacher
from .models import Student, GuardianContact
from .forms import StudentForm, GuardianContactForm, PromoteStudentsForm
from .filters import StudentFilter


from django_tables2 import SingleTableMixin
from .tables import StudentTable


class StudentListView(LoginRequiredMixin, RoleRequiredMixin, SingleTableMixin, ListView):
    model = Student
    table_class = StudentTable
    table_pagination = {'per_page': 20}
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    allowed_roles = ['admin', 'teacher']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # ST-19: teachers only see students in the classes they teach.
        if not user.is_superuser and user.role == 'teacher':
            teacher = Teacher.objects.filter(user=user).first()
            if teacher:
                pairs = teacher.assignments.values_list('class_name', 'stream').distinct()
                from django.db.models import Q
                q = Q()
                for cls, stream in pairs:
                    q |= Q(class_name=cls, stream=stream)
                qs = qs.filter(q) if pairs else qs.none()
            else:
                qs = qs.none()
        self.filterset = StudentFilter(self.request.GET, queryset=qs)
        return self.filterset.qs

    def get_table_data(self):
        data = list(super().get_table_data())
        is_admin = self.request.user.is_superuser or self.request.user.role == 'admin'
        for s in data:
            s.can_edit_flag = is_admin
        return data

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter'] = self.filterset
        return ctx


class StudentDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'
    allowed_roles = ['admin', 'teacher', 'parent']

    def get_context_data(self, **kwargs):
        # ST-20/22/23/24: profile shows attendance, fees, and grades history.
        ctx = super().get_context_data(**kwargs)
        student = self.object
        ctx['recent_attendance'] = student.attendance_records.all()[:10]
        ctx['transactions'] = student.transactions.all()[:10]
        ctx['grades'] = student.grade_records.all()[:10]
        ctx['guardian_contacts'] = student.guardian_contacts.all()
        return ctx


class StudentCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('students:list')
    allowed_roles = ['admin']

    def form_valid(self, form):
        messages.success(self.request, f'Student {form.instance.full_name} added successfully.')
        return super().form_valid(form)


class StudentUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('students:list')
    allowed_roles = ['admin']

    def form_valid(self, form):
        messages.success(self.request, f'Student {form.instance.full_name} updated.')
        return super().form_valid(form)


class StudentDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    """ST-03: delete with confirmation. Prefer archiving (see StudentArchiveView)
    over hard delete when fee/attendance/grade history should be preserved."""
    model = Student
    template_name = 'students/student_confirm_delete.html'
    success_url = reverse_lazy('students:list')
    allowed_roles = ['admin']

    def form_valid(self, form):
        messages.warning(self.request, 'Student record deleted.')
        return super().form_valid(form)


class StudentArchiveView(LoginRequiredMixin, RoleRequiredMixin, View):
    """ST-04/30/31/32/33: soft-archive instead of deleting, preserving
    fee/attendance/grade history. Status change is itself tracked by
    simple_history on the Student model."""
    allowed_roles = ['admin']

    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        new_status = request.POST.get('status')
        if new_status in Student.Status.values:
            student.status = new_status
            student.save(update_fields=['status'])
            messages.success(request, f'{student.full_name} status changed to {student.get_status_display()}.')
        return redirect('students:detail', pk=pk)


class PromoteStudentsView(LoginRequiredMixin, RoleRequiredMixin, View):
    """ST-12: bulk-promote every student in a class/stream to the next class."""
    allowed_roles = ['admin']

    def get(self, request):
        return render(request, 'students/promote_students.html', {'form': PromoteStudentsForm()})

    def post(self, request):
        form = PromoteStudentsForm(request.POST)
        if form.is_valid():
            qs = Student.objects.filter(
                class_name=form.cleaned_data['class_name'],
                stream=form.cleaned_data['stream'],
                status=Student.Status.ACTIVE,
            )
            count = qs.update(class_name=form.cleaned_data['new_class_name'])
            messages.success(request, f'Promoted {count} students to {form.cleaned_data["new_class_name"]}.')
            return redirect('students:list')
        return render(request, 'students/promote_students.html', {'form': form})


class GuardianContactCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    """ST-08: add an extra guardian/contact to a student."""
    model = GuardianContact
    form_class = GuardianContactForm
    template_name = 'students/guardian_contact_form.html'
    allowed_roles = ['admin']

    def dispatch(self, request, *args, **kwargs):
        self.student = get_object_or_404(Student, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.student = self.student
        messages.success(self.request, f'Guardian contact added for {self.student.full_name}.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('students:detail', kwargs={'pk': self.student.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['student'] = self.student
        return ctx


class MyChildrenView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    """Parent portal: list of the logged-in parent's children."""
    model = Student
    template_name = 'students/my_children.html'
    context_object_name = 'children'
    allowed_roles = ['parent']

    def get_queryset(self):
        return Student.objects.filter(guardians=self.request.user)
