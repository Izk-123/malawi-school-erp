from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import GradeRecord


@admin.register(GradeRecord)
class GradeRecordAdmin(ModelAdmin):
    list_display = ('student', 'subject', 'exam', 'score', 'grade')
    list_filter = ('subject', 'exam')
    search_fields = ('student__full_name',)
