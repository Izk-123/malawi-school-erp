from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import TimetablePeriod


@admin.register(TimetablePeriod)
class TimetablePeriodAdmin(ModelAdmin):
    list_display = ('day', 'start_time', 'end_time', 'subject', 'teacher', 'class_name', 'stream')
    list_filter = ('day', 'class_name', 'stream')
