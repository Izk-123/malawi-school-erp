from django.contrib import admin
from django.db.models import Count
from unfold.admin import ModelAdmin, TabularInline
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import (
    ExamSession, Subject, Paper, SyllabusTopic, AssessmentObjective,
    GradeDescriptor, ManebGradeScale, TopicCoverage,
)
from .resources import SubjectResource, SyllabusTopicResource


class PaperInline(TabularInline):
    model = Paper
    extra = 1


class GradeDescriptorInline(TabularInline):
    model = GradeDescriptor
    extra = 0


@admin.register(Subject)
class SubjectAdmin(ImportExportModelAdmin, SimpleHistoryAdmin, ModelAdmin):
    """SY-41/43: admin CRUD for subjects, with usage counts."""
    resource_class = SubjectResource
    list_display = ('code', 'name', 'category', 'is_elective', 'is_active', 'topic_count', 'grade_record_count')
    list_filter = ('category', 'is_elective', 'is_active')
    search_fields = ('code', 'name')
    inlines = [PaperInline, GradeDescriptorInline]

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


@admin.register(Paper)
class PaperAdmin(ModelAdmin):
    list_display = ('subject', 'number', 'paper_type', 'duration_minutes', 'total_marks')
    list_filter = ('paper_type', 'subject')


class AssessmentObjectiveInline(TabularInline):
    model = AssessmentObjective
    extra = 1


class SubtopicInline(TabularInline):
    """SY-42: shows subtopics nested under their parent in the admin."""
    model = SyllabusTopic
    fk_name = 'parent'
    extra = 0
    fields = ('code', 'title', 'order', 'is_active')


@admin.register(SyllabusTopic)
class SyllabusTopicAdmin(ImportExportModelAdmin, SimpleHistoryAdmin, ModelAdmin):
    resource_class = SyllabusTopicResource
    list_display = ('code', 'title', 'subject', 'parent', 'order', 'is_active', 'usage_count')
    list_filter = ('subject', 'is_active')
    search_fields = ('code', 'title')
    inlines = [AssessmentObjectiveInline, SubtopicInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_usage_count=Count('grade_records', distinct=True))

    @admin.display(description='Grade records', ordering='_usage_count')
    def usage_count(self, obj):
        return obj._usage_count


@admin.register(GradeDescriptor)
class GradeDescriptorAdmin(ModelAdmin):
    list_display = ('subject', 'paper', 'grade_band')
    list_filter = ('grade_band', 'subject')


@admin.register(ManebGradeScale)
class ManebGradeScaleAdmin(ModelAdmin):
    list_display = ('grade_number', 'label', 'gce_equivalent')


@admin.register(ExamSession)
class ExamSessionAdmin(ModelAdmin):
    list_display = ('name', 'exam_year', 'is_current', 'date_effective')
    list_filter = ('is_current',)


@admin.register(TopicCoverage)
class TopicCoverageAdmin(ModelAdmin):
    list_display = ('topic', 'teacher', 'class_name', 'stream', 'is_covered', 'covered_on')
    list_filter = ('is_covered', 'class_name')
