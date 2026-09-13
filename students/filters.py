"""ST-16: advanced filtering for the student list."""
import django_filters
from django import forms
from .models import Student


class StudentFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='filter_search', label='Search')
    class_name = django_filters.CharFilter(field_name='class_name', lookup_expr='icontains')
    stream = django_filters.ChoiceFilter(choices=[('A', 'A'), ('B', 'B')])
    status = django_filters.ChoiceFilter(choices=Student.Status.choices)
    gender = django_filters.ChoiceFilter(choices=Student.Gender.choices)

    class Meta:
        model = Student
        fields = ['q', 'class_name', 'stream', 'status', 'gender']

    def filter_search(self, queryset, name, value):
        # ST-15: search by name, student ID, guardian name, or phone.
        from django.db.models import Q
        return queryset.filter(
            Q(full_name__icontains=value)
            | Q(student_id__icontains=value)
            | Q(guardian_name__icontains=value)
            | Q(guardian_phone__icontains=value)
        )
