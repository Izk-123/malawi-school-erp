from django.contrib import admin
from unfold.admin import ModelAdmin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin
from .models import Student, GuardianContact
from .resources import StudentResource


class GuardianContactInline(admin.TabularInline):
    model = GuardianContact
    extra = 1


@admin.action(description='Mark selected students as Graduated')
def mark_graduated(modeladmin, request, queryset):
    queryset.update(status=Student.Status.GRADUATED)


@admin.action(description='Mark selected students as Transferred')
def mark_transferred(modeladmin, request, queryset):
    queryset.update(status=Student.Status.TRANSFERRED)


@admin.register(Student)
class StudentAdmin(ImportExportModelAdmin, SimpleHistoryAdmin, ModelAdmin):
    resource_class = StudentResource
    list_display = ('student_id', 'full_name', 'class_name', 'stream', 'status', 'fee_status_display')
    list_filter = ('class_name', 'stream', 'status', 'gender')
    search_fields = ('full_name', 'student_id', 'guardian_name', 'guardian_phone')
    filter_horizontal = ('guardians', 'enrolled_subjects')
    inlines = [GuardianContactInline]
    actions = [mark_graduated, mark_transferred]

    @admin.display(description='Fees')
    def fee_status_display(self, obj):
        return obj.fee_status


@admin.register(GuardianContact)
class GuardianContactAdmin(ModelAdmin):
    list_display = ('name', 'student', 'relationship', 'phone_number', 'is_primary')
    list_filter = ('relationship', 'is_primary')
