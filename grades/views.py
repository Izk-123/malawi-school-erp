from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView

from accounts.mixins import RoleRequiredMixin
from students.models import Student
from notifications.tasks import notify_grade_published
from .models import GradeRecord
from .forms import GradeRecordForm


class GradeListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = GradeRecord
    template_name = 'grades/grade_list.html'
    context_object_name = 'grades'
    allowed_roles = ['admin', 'teacher', 'parent']
    paginate_by = 30


class GradeCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = GradeRecord
    form_class = GradeRecordForm
    template_name = 'grades/grade_form.html'
    success_url = reverse_lazy('grades:list')
    allowed_roles = ['admin', 'teacher']

    def form_valid(self, form):
        form.instance.recorded_by = self.request.user
        response = super().form_valid(form)
        notify_grade_published.delay(form.instance.id)
        messages.success(self.request, 'Grade recorded and student notified.')
        return response


class GradeDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = GradeRecord
    template_name = 'grades/grade_confirm_delete.html'
    success_url = reverse_lazy('grades:list')
    allowed_roles = ['admin', 'teacher']


class MyGradesView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    template_name = 'grades/my_grades.html'
    context_object_name = 'grades'
    allowed_roles = ['student']

    def get_queryset(self):
        student = Student.objects.filter(user=self.request.user).first()
        self.student = student
        return GradeRecord.objects.filter(student=student) if student else GradeRecord.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['student'] = self.student
        return ctx
