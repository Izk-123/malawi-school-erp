import django_filters
from .models import StaffMember


class StaffFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search', label='Search')
    department = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = StaffMember
        fields = ['search', 'department', 'status']

    def filter_search(self, queryset, name, value):
        from django.db.models import Q
        return queryset.filter(Q(full_name__icontains=value) | Q(staff_id__icontains=value))
