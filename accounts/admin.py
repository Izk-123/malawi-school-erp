from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from unfold.admin import ModelAdmin
from import_export.admin import ImportExportModelAdmin
from import_export import resources

from .models import (
    User, AuditLog, PasswordHistory, InvitationToken, ApprovalRequest,
)


class UserResource(resources.ModelResource):
    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name', 'email',
            'role', 'phone_number', 'is_active',
        )
        export_order = fields
        import_id_fields = ('username',)


@admin.register(User)
class CustomUserAdmin(ImportExportModelAdmin, UserAdmin, ModelAdmin):
    resource_class = UserResource
    list_display = (
        'username', 'first_name', 'last_name', 'role',
        'email', 'is_active', 'two_factor_enabled',
    )
    list_filter = ('role', 'is_active', 'is_staff', 'two_factor_enabled')
    fieldsets = UserAdmin.fieldsets + (
        ('School Role', {
            'fields': ('role', 'phone_number', 'profile_picture', 'preferred_language'),
        }),
        ('Governance', {
            'fields': (
                'created_by', 'approved_by', 'activated_at',
                'two_factor_enabled', 'must_change_password',
            ),
        }),
    )
    readonly_fields = ('activated_at',)


@admin.register(AuditLog)
class AuditLogAdmin(ModelAdmin):
    list_display = (
        'created_at', 'user', 'target_user', 'action', 'method', 'reason',
    )
    list_filter = ('action', 'method')
    search_fields = ('username_attempted', 'user__username', 'target_user__username')
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PasswordHistory)
class PasswordHistoryAdmin(ModelAdmin):
    list_display = ('user', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(InvitationToken)
class InvitationTokenAdmin(ModelAdmin):
    list_display = (
        'purpose', 'proposed_username', 'invited_phone', 'invited_email',
        'issued_by', 'approved_by', 'used', 'expires_at',
    )
    list_filter = ('purpose', 'used', 'delivery_method')
    search_fields = ('proposed_username', 'invited_phone', 'invited_email')
    readonly_fields = [f.name for f in InvitationToken._meta.fields]

    def has_add_permission(self, request):
        # Invitations must go through services.issue_invitation so the
        # permission gate and audit log fire. No admin back door.
        return False


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(ModelAdmin):
    list_display = (
        'purpose', 'proposed_username', 'created_by', 'status', 'created_at',
    )
    list_filter = ('purpose', 'status')
    search_fields = ('proposed_username', 'proposed_phone', 'proposed_email')
    readonly_fields = (
        'created_by', 'created_at', 'decided_by', 'decided_at', 'invitation',
    )