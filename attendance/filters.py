"""AT-08/AT-09/AT-11/AT-25: filtering for history/summary/export views."""
import django_filters
from .models import AttendanceRecord


class AttendanceFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte', label='From')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte', label='To')
    class_name = django_filters.CharFilter(field_name='class_name_at_time', lookup_expr='icontains')
    stream = django_filters.ChoiceFilter(field_name='stream_at_time', choices=[('A', 'A'), ('B', 'B')])
    status = django_filters.ChoiceFilter(choices=AttendanceRecord.Status.choices)

    class Meta:
        model = AttendanceRecord
        fields = ['date_from', 'date_to', 'class_name', 'stream', 'status']
