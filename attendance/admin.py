from django.contrib import admin
from unfold.admin import ModelAdmin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin
from .models import AttendanceRecord, Holiday
from .resources import AttendanceResource


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(ImportExportModelAdmin, SimpleHistoryAdmin, ModelAdmin):
    resource_class = AttendanceResource
    list_display = ('student', 'date', 'status', 'class_name_at_time', 'stream_at_time', 'marked_by', 'marked_at')
    list_filter = ('status', 'date', 'class_name_at_time')
    search_fields = ('student__full_name',)
    readonly_fields = ('marked_at', 'updated_at')


@admin.register(Holiday)
class HolidayAdmin(ModelAdmin):
    list_display = ('date', 'name')
