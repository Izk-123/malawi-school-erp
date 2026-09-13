from import_export import resources

from .models import User


class UserResource(resources.ModelResource):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'phone_number', 'is_active')
        import_id_fields = ('username',)