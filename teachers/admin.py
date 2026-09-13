from django.contrib import admin
from unfold.admin import ModelAdmin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from simple_history.admin import SimpleHistoryAdmin
from .models import Teacher, ClassAssignment, Subject, TeacherCertification


class TeacherResource(resources.ModelResource):
    class Meta:
        model = Teacher
        fields = ('teacher_id', 'full_name', 'subject', 'qualification', 'phone_number', 'email', 'status')
        export_order = fields
        import_id_fields = ('teacher_id',)


class ClassAssignmentInline(admin.TabularInline):
    model = ClassAssignment
    extra = 1


class TeacherCertificationInline(admin.TabularInline):
    model = TeacherCertification
    extra = 1


@admin.register(Teacher)
class TeacherAdmin(ImportExportModelAdmin, SimpleHistoryAdmin, ModelAdmin):
    resource_class = TeacherResource
    list_display = ('teacher_id', 'full_name', 'subject', 'status')
    list_filter = ('status', 'subject')
    search_fields = ('full_name', 'teacher_id', 'phone_number')
    filter_horizontal = ('subjects', 'syllabus_subjects', 'syllabus_papers')
    inlines = [ClassAssignmentInline, TeacherCertificationInline]


@admin.register(Subject)
class SubjectAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
