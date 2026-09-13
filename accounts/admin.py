from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from unfold.admin import ModelAdmin
from import_export.admin import ImportExportModelAdmin
from import_export import resources

from .models import User, AuditLog, PasswordHistory


class UserResource(resources.ModelResource):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'role', 'phone_number', 'is_active')
        export_order = fields
        import_id_fields = ('username',)


@admin.register(User)
class CustomUserAdmin(ImportExportModelAdmin, UserAdmin, ModelAdmin):
    resource_class = UserResource
    list_display = ('username', 'first_name', 'last_name', 'role', 'email', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('School Role', {'fields': ('role', 'phone_number', 'profile_picture', 'preferred_language')}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(ModelAdmin):
    list_display = ('created_at', 'user', 'username_attempted', 'action', 'ip_address')
    list_filter = ('action',)
    search_fields = ('username_attempted', 'user__username')
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
