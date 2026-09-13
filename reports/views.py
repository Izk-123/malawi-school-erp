from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
import csv

from accounts.mixins import RoleRequiredMixin, role_required
from students.models import Student
from django.contrib.auth.decorators import login_required


class ReportsIndexView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ['admin', 'teacher', 'staff']

    def get(self, request):
        students = Student.objects.all()
        males = students.filter(gender='Male').count()
        females = students.filter(gender='Female').count()
        avg_attendance = round(
            sum(s.attendance_percentage for s in students) / students.count(), 1
        ) if students.count() else 0
        total_paid = sum(s.fees_paid for s in students)

        classes = {}
        for s in students:
            key = s.class_display
            classes[key] = classes.get(key, 0) + 1

        grades = {}
        for s in students:
            if s.average_grade and s.average_grade != 'N/A':
                grades[s.average_grade] = grades.get(s.average_grade, 0) + 1

        context = {
            'total_students': students.count(),
            'males': males,
            'females': females,
            'avg_attendance': avg_attendance,
            'total_paid': total_paid,
            'classes': classes,
            'grades': grades,
        }
        return render(request, 'reports/index.html', context)


@login_required
@role_required('admin', 'teacher', 'staff')
def export_students_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students.csv"'
    writer = csv.writer(response)
    writer.writerow(['Student ID', 'Name', 'Class', 'Attendance %', 'Avg Grade', 'Fees Balance'])
    for s in Student.objects.all():
        writer.writerow([s.student_id, s.full_name, s.class_display, s.attendance_percentage, s.average_grade, s.balance])
    return response
