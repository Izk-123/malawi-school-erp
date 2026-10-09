"""Django admin registration for the teachers app.

``TeacherAdmin`` uses ``TeacherForm`` so the admin surfaces the same
validation as the web form, and hosts two inlines that were added with the
TCM layer: ``TeacherQualificationInline`` and ``TCMLicenseRenewalInline``.

The bulk action "Send TCM renewal reminder" reuses the same window
selection and AuditLog-backed dedupe as the daily Celery sweep
(``teachers.tasks.send_tcm_expiry_reminders``), so a manual send cannot
double-message a teacher the automatic sweep is about to touch.
"""
from django.contrib import admin, messages
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from simple_history.admin import SimpleHistoryAdmin

from .forms import TeacherForm
from .models import (
    ClassAssignment,
    GradePromotion,
    Subject,
    TCMLicenseRenewal,
    Teacher,
    TeacherCertification,
    TeacherQualification,
)


# ---------------------------------------------------------------------------
# Import / export
# ---------------------------------------------------------------------------
class TeacherResource(resources.ModelResource):
    """Bulk export / import for the teachers register.

    ``import_id_fields = ('teacher_id',)`` — import requires the TCM-style
    school ID (``TCH-YYYY-NNN``), so a bulk update matches existing rows
    rather than creating duplicates. New teachers should be created via
    the admin form; bulk import is for refreshing the register.
    """

    class Meta:
        model = Teacher
        fields = (
            'teacher_id', 'full_name', 'gender', 'national_id',
            'phone_number', 'email',
            # Legacy (kept in the export so existing spreadsheets still line up)
            'subject', 'qualification',
            # TCM
            'tcm_registration_number', 'tcm_status', 'tcm_license_expiry',
            # Academic
            'highest_academic_qualification', 'academic_institution',
            # Professional
            'professional_qualification', 'professional_institution',
            'year_qualified',
            # Level / grade / employment
            'teaching_level', 'government_grade', 'employment_type',
            'status', 'hired_on',
        )
        export_order = fields
        import_id_fields = ('teacher_id',)


# ---------------------------------------------------------------------------
# Inlines
# ---------------------------------------------------------------------------
class ClassAssignmentInline(admin.TabularInline):
    model = ClassAssignment
    extra = 1


class TeacherCertificationInline(admin.TabularInline):
    """CPD / workshop records — free-form, unchanged from before."""
    model = TeacherCertification
    extra = 1


class TeacherQualificationInline(admin.TabularInline):
    """Formal academic / professional credentials.

    ``extra = 0`` because qualifications are recorded facts — a teacher
    acquires one when they graduate, not speculatively on every edit.
    The admin clicks "Add another" only when there's a new one to record.
    """
    model = TeacherQualification
    extra = 0
    fields = (
        'qualification_type', 'institution', 'year_obtained',
        'verified', 'certificate',
    )


class TCMLicenseRenewalInline(admin.TabularInline):
    """History of TCM license renewals.

    Read-mostly: HR records a renewal when the receipt comes in, and the
    teacher's ``tcm_license_expiry`` / ``tcm_status`` are rolled up from
    the latest row by a service-layer call in the (future) renewal view.
    The inline is here so the full history is visible when editing a
    teacher record.
    """
    model = TCMLicenseRenewal
    extra = 0
    fields = (
        'renewed_at', 'expires_at', 'receipt_number',
        'renewal_fee_paid', 'document',
    )


# ---------------------------------------------------------------------------
# Colour map for the TCM status badge.
#
# Keys match ``Teacher.TCMStatus`` values. Values are (foreground, background)
# hex pairs, chosen to read on both light and dark Unfold themes.
# ---------------------------------------------------------------------------
_TCM_BADGE_COLOURS = {
    Teacher.TCMStatus.REGISTERED:     ('#14532d', '#dcfce7'),
    Teacher.TCMStatus.PROVISIONAL:    ('#78350f', '#fef3c7'),
    Teacher.TCMStatus.SUSPENDED:      ('#7f1d1d', '#fee2e2'),
    Teacher.TCMStatus.EXPIRED:        ('#7f1d1d', '#fee2e2'),
    Teacher.TCMStatus.NOT_REGISTERED: ('#374151', '#e5e7eb'),
}


# ---------------------------------------------------------------------------
# Teacher admin
# ---------------------------------------------------------------------------
@admin.register(Teacher)
class TeacherAdmin(ImportExportModelAdmin, SimpleHistoryAdmin, ModelAdmin):
    form = TeacherForm
    resource_class = TeacherResource

    # -- List view ----------------------------------------------------------
    list_display = (
        'teacher_id', 'full_name', 'subject',
        'tcm_status_badge', 'government_grade',
        'teaching_level', 'employment_type', 'status',
    )
    list_filter = (
        'tcm_status', 'teaching_level', 'employment_type',
        'professional_qualification', 'government_grade',
        'status', 'subject',
    )
    search_fields = (
        'full_name', 'teacher_id', 'phone_number',
        'national_id', 'tcm_registration_number',
    )
    list_per_page = 30
    ordering = ('full_name',)

    # -- Form layout --------------------------------------------------------
    fieldsets = (
        ('Identity', {
            'fields': (
                'teacher_id', 'full_name', 'photo',
                'gender', 'date_of_birth', 'national_id', 'user',
            ),
        }),
        ('Contact', {
            'fields': ('phone_number', 'email', 'address'),
        }),
        ('Legacy specialisation', {
            'classes': ('collapse',),
            'description': (
                'Free-text fields kept for backwards compatibility with '
                'existing templates and reports. Prefer the structured '
                'fields below for new records.'
            ),
            'fields': ('subject', 'subjects', 'qualification'),
        }),
        ('TCM registration', {
            'description': (
                'A teacher with a valid TCM license in Registered or '
                'Provisional status may be assigned to a class. All other '
                'statuses block assignment.'
            ),
            'fields': (
                'tcm_registration_number', 'tcm_status', 'tcm_license_expiry',
                'has_valid_tcm_license_display', 'tcm_days_until_expiry_display',
            ),
        }),
        ('Academic qualifications', {
            'fields': (
                'highest_academic_qualification', 'academic_institution',
            ),
        }),
        ('Professional qualifications', {
            'fields': (
                'professional_qualification', 'professional_institution',
                'year_qualified', 'is_unqualified_display',
            ),
        }),
        ('Teaching level and grade', {
            'fields': ('teaching_level', 'government_grade'),
        }),
        ('Employment', {
            'fields': ('employment_type', 'hired_on', 'status'),
        }),
        ('Syllabus (MANEB)', {
            'classes': ('collapse',),
            'fields': ('syllabus_subjects', 'syllabus_papers'),
        }),
    )

    readonly_fields = (
        'teacher_id',
        'hired_on',
        # Computed (model properties surfaced as read-only rows):
        'has_valid_tcm_license_display',
        'tcm_days_until_expiry_display',
        'is_unqualified_display',
    )

    filter_horizontal = ('subjects', 'syllabus_subjects', 'syllabus_papers')

    inlines = [
        ClassAssignmentInline,
        TeacherQualificationInline,
        TCMLicenseRenewalInline,
        TeacherCertificationInline,
    ]

    actions = ('send_tcm_renewal_reminder',)

    # -- Computed display columns -------------------------------------------

    @admin.display(description='TCM status', ordering='tcm_status')
    def tcm_status_badge(self, obj):
        """Colour-coded TCM status pill.

        Uses inline styles rather than admin CSS classes so it renders
        identically regardless of the Unfold theme or version.
        """
        fg, bg = _TCM_BADGE_COLOURS.get(
            obj.tcm_status, ('#374151', '#e5e7eb'),
        )
        return format_html(
            '<span style="display:inline-block;padding:2px 9px;'
            'border-radius:10px;font-size:11px;font-weight:600;'
            'color:{};background:{};white-space:nowrap;">{}</span>',
            fg, bg, obj.get_tcm_status_display(),
        )

    @admin.display(description='TCM valid?', boolean=True)
    def has_valid_tcm_license_display(self, obj):
        return obj.has_valid_tcm_license

    @admin.display(description='Days to expiry')
    def tcm_days_until_expiry_display(self, obj):
        days = obj.tcm_days_until_expiry
        if days is None:
            return '—'
        if days < 0:
            return f'expired {abs(days)} day(s) ago'
        if days == 0:
            return 'expires today'
        return f'{days} day(s)'

    @admin.display(description='Qualified?', boolean=True)
    def is_unqualified_display(self, obj):
        """Shown inverted so the checkmark means 'good' (qualified)."""
        return not obj.is_unqualified

    # -- Bulk actions -------------------------------------------------------

    @admin.action(description='Send TCM renewal reminder to selected teachers')
    def send_tcm_renewal_reminder(self, request, queryset):
        """Dispatch one reminder per selected teacher.

        Uses the same window selection and AuditLog-backed dedupe as the
        daily automatic sweep, so a manual send suppresses the
        corresponding automatic window reminder and vice versa. Teachers
        whose TCM status is not renewable, or whose license is not close
        enough to expiry to warrant a nudge, are reported as 'skipped'.
        """
        from .tasks import send_manual_tcm_reminder

        sent = skipped = failed = 0
        for teacher in queryset:
            result = send_manual_tcm_reminder(teacher)
            if result == 'sent':
                sent += 1
            elif result == 'skipped':
                skipped += 1
            else:
                failed += 1

        parts = [f'{sent} reminder(s) sent']
        if skipped:
            parts.append(f'{skipped} skipped')
        if failed:
            parts.append(f'{failed} failed (see server log)')

        level = messages.WARNING if failed else messages.SUCCESS
        self.message_user(request, ', '.join(parts) + '.', level=level)


# ---------------------------------------------------------------------------
# Standalone registrations
# ---------------------------------------------------------------------------
@admin.register(Subject)
class SubjectAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(TCMLicenseRenewal)
class TCMLicenseRenewalAdmin(ModelAdmin):
    """Standalone view of every renewal — useful for HR audits without
    walking into each teacher record.
    """
    list_display = ('teacher', 'renewed_at', 'expires_at', 'receipt_number', 'renewal_fee_paid')
    list_filter = ('renewed_at', 'expires_at')
    search_fields = ('teacher__full_name', 'teacher__teacher_id', 'receipt_number')
    autocomplete_fields = ('teacher',)
    date_hierarchy = 'renewed_at'


@admin.register(TeacherQualification)
class TeacherQualificationAdmin(ModelAdmin):
    list_display = ('teacher', 'qualification_type', 'institution', 'year_obtained', 'verified')
    list_filter = ('qualification_type', 'verified', 'year_obtained')
    search_fields = ('teacher__full_name', 'teacher__teacher_id', 'institution')
    autocomplete_fields = ('teacher',)


@admin.register(GradePromotion)
class GradePromotionAdmin(ModelAdmin):
    list_display = ('teacher', 'from_grade', 'to_grade', 'promoted_at', 'approved_by')
    list_filter = ('from_grade', 'to_grade', 'promoted_at')
    search_fields = ('teacher__full_name', 'teacher__teacher_id')
    autocomplete_fields = ('teacher', 'approved_by')
    date_hierarchy = 'promoted_at'