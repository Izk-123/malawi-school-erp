"""TC-20/21: search/filter for the teacher list."""
import django_filters
from .models import Teacher


class TeacherFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='filter_search', label='Search')
    subject = django_filters.CharFilter(field_name='subject', lookup_expr='icontains')
    status = django_filters.ChoiceFilter(choices=Teacher.Status.choices)
    qualification = django_filters.CharFilter(field_name='qualification', lookup_expr='icontains')

    class Meta:
        model = Teacher
        fields = ['q', 'subject', 'status', 'qualification']

    def filter_search(self, queryset, name, value):
        from django.db.models import Q
        return queryset.filter(
            Q(full_name__icontains=value) | Q(teacher_id__icontains=value)
            | Q(subject__icontains=value) | Q(phone_number__icontains=value)
        )
