from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import User


class RoleAwareLoginForm(AuthenticationForm):
    """AC-07: login form includes a role selector. The account's *actual*
    role (from the database) is still the source of truth for RBAC - this
    field just confirms the user is signing into the portal they expect
    and gives a friendlier error if they pick the wrong one."""
    role = forms.ChoiceField(choices=User.Role.choices, widget=forms.Select(attrs={'class': 'form-select'}))

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        selected_role = self.cleaned_data.get('role')
        if selected_role and user.role != selected_role and not user.is_superuser:
            raise forms.ValidationError(
                f"This account isn't registered as {dict(User.Role.choices).get(selected_role)}. "
                f"Please choose \"{user.get_role_display()}\" instead.",
                code='role_mismatch',
            )


class SelfRegistrationForm(UserCreationForm):
    """AC-02: self-registration, limited to Student/Parent roles."""
    role = forms.ChoiceField(choices=[
        (User.Role.STUDENT, 'Student'),
        (User.Role.PARENT, 'Parent'),
    ])
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(required=False, help_text='e.g. +265991234567')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Create Account'))


class UserCreateForm(UserCreationForm):
    """AC-01: admin-created accounts for any role."""
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'phone_number')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Create User'))


class UserUpdateForm(UserChangeForm):
    """AC-22: admin can view/edit any user's profile including role."""
    password = None

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'phone_number',
                   'profile_picture', 'is_active')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Changes'))


class ProfileForm(forms.ModelForm):
    """AC-21: users can edit their own basic profile fields (not role)."""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'profile_picture', 'preferred_language')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Profile'))
