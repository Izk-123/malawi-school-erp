import django_filters
from .models import Applicant, Enquiry


class EnquiryFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='filter_search', label='Search')
    status = django_filters.ChoiceFilter(choices=Enquiry.Status.choices)
    source = django_filters.ChoiceFilter(choices=Enquiry.Source.choices)

    class Meta:
        model = Enquiry
        fields = ['status', 'source']

    def filter_search(self, queryset, name, value):
        from django.db.models import Q
        return queryset.filter(
            Q(student_name__icontains=value)
            | Q(parent_name__icontains=value)
            | Q(guardian_phone__icontains=value)
        )


class ApplicantFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='filter_search', label='Search')
    status = django_filters.ChoiceFilter(choices=Applicant.Status.choices)
    applying_for = django_filters.CharFilter(lookup_expr='icontains')
    min_score = django_filters.NumberFilter(field_name='composite_score', lookup_expr='gte')

    class Meta:
        model = Applicant
        fields = ['status', 'applying_for', 'min_score']

    def filter_search(self, queryset, name, value):
        from django.db.models import Q
        return queryset.filter(
            Q(full_name__icontains=value)
            | Q(applicant_code__icontains=value)
            | Q(guardian_phone__icontains=value)
            | Q(pslce_number__icontains=value)
        )