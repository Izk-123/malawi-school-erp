from django.contrib import admin
from unfold.admin import ModelAdmin
from import_export.admin import ImportExportModelAdmin
from .models import FeeStructure, FeeTransaction, Discount


@admin.register(FeeStructure)
class FeeStructureAdmin(ModelAdmin):
    list_display = ('class_name', 'stream', 'term', 'total_amount')


@admin.register(FeeTransaction)
class FeeTransactionAdmin(ImportExportModelAdmin, ModelAdmin):
    list_display = ('receipt_no', 'student', 'amount', 'date', 'method', 'gateway', 'is_reversed')
    list_filter = ('method', 'date', 'is_reversed', 'gateway')
    search_fields = ('student__full_name', 'receipt_no', 'gateway_reference')
    readonly_fields = ('reversed_at', 'reversed_by')


@admin.register(Discount)
class DiscountAdmin(ModelAdmin):
    list_display = ('student', 'kind', 'discount_type', 'value', 'sponsor_name', 'is_active', 'effective_date')
    list_filter = ('kind', 'discount_type', 'is_active')
    search_fields = ('student__full_name', 'sponsor_name')
