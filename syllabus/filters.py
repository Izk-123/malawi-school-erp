"""SY-30/31/32: browse/search/filter for the syllabus."""
import django_filters
from .models import Subject, SyllabusTopic


class SubjectFilter(django_filters.FilterSet):
    category = django_filters.ChoiceFilter(choices=Subject.CORE_ELEMENTS)
    is_elective = django_filters.BooleanFilter()
    search = django_filters.CharFilter(method='filter_search', label='Search')

    class Meta:
        model = Subject
        fields = ['category', 'is_elective', 'search']

    def filter_search(self, queryset, name, value):
        from django.db.models import Q
        return queryset.filter(Q(name__icontains=value) | Q(code__icontains=value))


class TopicFilter(django_filters.FilterSet):
    subject = django_filters.CharFilter(field_name='subject__code')
    search = django_filters.CharFilter(method='filter_search', label='Search')

    class Meta:
        model = SyllabusTopic
        fields = ['subject', 'search']

    def filter_search(self, queryset, name, value):
        from django.db.models import Q
        return queryset.filter(
            Q(title__icontains=value) | Q(code__icontains=value) | Q(objectives__text__icontains=value)
        ).distinct()
