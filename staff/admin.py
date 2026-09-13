from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import StaffMember


@admin.register(StaffMember)
class StaffMemberAdmin(ModelAdmin):
    list_display = ('staff_id', 'full_name', 'position', 'department', 'status')
    list_filter = ('department', 'status')
    search_fields = ('full_name', 'staff_id')
