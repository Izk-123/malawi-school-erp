from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import PaymentTransaction


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(ModelAdmin):
    list_display = ('reference', 'student', 'gateway', 'amount', 'status', 'created_at')
    list_filter = ('gateway', 'status')
    search_fields = ('reference', 'gateway_reference', 'student__full_name')
    readonly_fields = ('reference', 'raw_initiation_response', 'raw_webhook_response', 'created_at', 'updated_at')
