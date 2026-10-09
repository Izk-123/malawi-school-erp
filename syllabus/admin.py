from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import (
    ExamSession, Subject, Paper, SyllabusTopic, AssessmentObjective,
    GradeDescriptor, ManebGradeScale, TopicCoverage,
)
from .resources import SubjectResource, SyllabusTopicResource


# ---------------------------------------------------------------------------
# Inlines
# ---------------------------------------------------------------------------

class PaperInline(TabularInline):
    model = Paper
    extra = 1
    fields = ('number', 'title', 'paper_type', 'duration_minutes', 'total_marks')


class GradeDescriptorInline(TabularInline):
    model = GradeDescriptor
    extra = 0
    fields = ('paper', 'grade_band', 'descriptor')


class AssessmentObjectiveInline(TabularInline):
    model = AssessmentObjective
    extra = 1
    fields = ('order', 'text', 'is_active')


class SubtopicInline(TabularInline):
    """SY-42: shows subtopics nested under their parent in the admin."""
    model = SyllabusTopic
    fk_name = 'parent'
    extra = 0
    fields = ('code', 'title', 'order', 'is_active')


# ---------------------------------------------------------------------------
# ExamSession
# ---------------------------------------------------------------------------

@admin.register(ExamSession)
class ExamSessionAdmin(ModelAdmin):
    list_display = ('name', 'exam_year', 'level', 'is_current', 'date_effective')
    list_filter = ('level', 'is_current', 'exam_year')
    search_fields = ('name',)
    list_editable = ('is_current',)
    ordering = ('-exam_year', 'level')


# ---------------------------------------------------------------------------
# Subject
# ---------------------------------------------------------------------------

@admin.register(Subject)
class SubjectAdmin(ImportExportModelAdmin, SimpleHistoryAdmin, ModelAdmin):
    """SY-41/43: admin CRUD for subjects, with usage counts."""
    resource_class = SubjectResource
    list_display = (
        'code', 'name', 'level', 'category', 'is_elective',
        'is_active', 'topic_count', 'grade_record_count',
    )
    list_filter = ('level', 'category', 'is_elective', 'is_active')
    search_fields = ('code', 'name')
    list_editable = ('is_active',)
    inlines = [PaperInline, GradeDescriptorInline]
    readonly_fields = ('paper_count_display',)

    fieldsets = (
        (None, {
            'fields': ('code', 'name', 'level', 'category', 'is_elective', 'is_active'),
        }),
        ('Description', {
            'fields': ('description',),
            'classes': ('collapse',),
        }),
        ('Usage', {
            'fields': ('paper_count_display',),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _topic_count=Count('topics', distinct=True),
            _grade_record_count=Count('grade_records', distinct=True),
        )

    @admin.display(description='Topics', ordering='_topic_count')
    def topic_count(self, obj):
        return obj._topic_count

    @admin.display(description='Grade records referencing this subject', ordering='_grade_record_count')
    def grade_record_count(self, obj):
        return obj._grade_record_count

    @admin.display(description='Papers')
    def paper_count_display(self, obj):
        if obj.pk is None:
            return '—'
        return obj.papers.count()


# ---------------------------------------------------------------------------
# Paper
# ---------------------------------------------------------------------------

@admin.register(Paper)
class PaperAdmin(ModelAdmin):
    list_display = ('subject', 'number', 'paper_type', 'duration_minutes', 'total_marks')
    list_filter = ('paper_type', 'subject__level', 'subject')
    search_fields = ('subject__code', 'subject__name', 'number', 'title')
    autocomplete_fields = ('subject',)


# ---------------------------------------------------------------------------
# SyllabusTopic
# ---------------------------------------------------------------------------

@admin.register(SyllabusTopic)
class SyllabusTopicAdmin(ImportExportModelAdmin, ModelAdmin):
    resource_class = SyllabusTopicResource
    list_display = (
        'code', 'title', 'subject', 'get_level', 'parent',
        'order', 'is_active', 'usage_count',
    )
    list_filter = ('subject__level', 'subject', 'is_active')
    search_fields = ('code', 'title', 'subject__code', 'subject__name')
    list_editable = ('order', 'is_active')
    autocomplete_fields = ('subject', 'paper', 'parent')
    inlines = [AssessmentObjectiveInline, SubtopicInline]
    ordering = ('subject', 'tree_id', 'lft')

    fieldsets = (
        (None, {
            'fields': ('subject', 'paper', 'parent'),
        }),
        ('Topic', {
            'fields': ('code', 'title', 'core_element', 'order', 'is_active'),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'subject', 'parent', 'paper',
        ).annotate(_usage_count=Count('grade_records', distinct=True))

    @admin.display(description='Level', ordering='subject__level')
    def get_level(self, obj):
        return obj.subject.level

    @admin.display(description='Grade records', ordering='_usage_count')
    def usage_count(self, obj):
        return obj._usage_count


# ---------------------------------------------------------------------------
# AssessmentObjective
# ---------------------------------------------------------------------------

@admin.register(AssessmentObjective)
class AssessmentObjectiveAdmin(ModelAdmin):
    list_display = ('__str__', 'topic', 'get_level', 'order', 'is_active')
    list_filter = ('is_active', 'topic__subject__level', 'topic__subject')
    search_fields = ('text', 'topic__code', 'topic__title')
    autocomplete_fields = ('topic',)
    list_editable = ('order', 'is_active')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('topic', 'topic__subject')

    @admin.display(description='Level', ordering='topic__subject__level')
    def get_level(self, obj):
        return obj.topic.subject.level


# ---------------------------------------------------------------------------
# GradeDescriptor
# ---------------------------------------------------------------------------

@admin.register(GradeDescriptor)
class GradeDescriptorAdmin(ModelAdmin):
    list_display = ('subject', 'paper', 'grade_band')
    list_filter = ('grade_band', 'subject__level', 'subject')
    search_fields = ('subject__code', 'subject__name', 'descriptor')
    autocomplete_fields = ('subject', 'paper')


# ---------------------------------------------------------------------------
# ManebGradeScale
# ---------------------------------------------------------------------------

@admin.register(ManebGradeScale)
class ManebGradeScaleAdmin(ModelAdmin):
    list_display = ('grade_number', 'label', 'gce_equivalent')
    list_filter = ('label', 'gce_equivalent')
    search_fields = ('label', 'description')
    ordering = ('grade_number',)


# ---------------------------------------------------------------------------
# TopicCoverage
# ---------------------------------------------------------------------------

@admin.register(TopicCoverage)
class TopicCoverageAdmin(ModelAdmin):
    list_display = ('topic', 'teacher', 'class_name', 'stream', 'is_covered', 'covered_on')
    list_filter = ('is_covered', 'class_name', 'stream', 'topic__subject__level')
    search_fields = (
        'topic__code', 'topic__title',
        'teacher__user__username', 'teacher__user__first_name', 'teacher__user__last_name',
    )
    autocomplete_fields = ('topic', 'teacher')
    date_hierarchy = 'covered_on'
    list_editable = ('is_covered',)