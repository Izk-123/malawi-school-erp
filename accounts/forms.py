"""Forms for the accounts app.

Notes:
  - SchoolLoginForm: username *or* email, no role dropdown (AC-07a).
  - SelfRegistrationForm: Student/Parent only, normalises Malawian phone
    numbers to the canonical +265XXXXXXXXX form.
  - UserCreateForm/UserUpdateForm: admin-only, any role.
  - ProfileForm: self-service, role cannot be changed here.
"""
from django import forms
from django.contrib.auth.forms import (
    UserCreationForm,
    UserChangeForm,
    AuthenticationForm,
)
from django.core.validators import RegexValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from common.forms import enable_dropzone
from .models import User


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
class SchoolLoginForm(AuthenticationForm):
    """
    AC-07a: login is username-or-email + password only. The account's role
    (from the database) is the sole source of truth for which dashboard the
    user lands on, so the user never has to declare a role.
    """
    username = forms.CharField(
        label='Username or Email',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autofocus': True,
            'autocomplete': 'username',
        }),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'current-password',
        }),
    )

    def clean_username(self):
        value = self.cleaned_data['username'].strip()
        if '@' in value:
            match = User.objects.filter(email__iexact=value).first()
            if not match:
                raise forms.ValidationError('No account found with that email.')
            return match.username
        return value


# ---------------------------------------------------------------------------
# Self-registration (Student / Parent only)
# ---------------------------------------------------------------------------
_MALAWI_PHONE_VALIDATOR = RegexValidator(
    r'^\+265\d{9}$',
    'Enter a valid Malawian number (9 digits after +265).',
)


class SelfRegistrationForm(UserCreationForm):
    """AC-02: self-registration, limited to Student/Parent roles."""
    role = forms.ChoiceField(choices=[
        (User.Role.STUDENT, 'Student'),
        (User.Role.PARENT, 'Parent'),
    ])
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(
        required=False,
        help_text='9 digits after +265, e.g. 991234567',
        widget=forms.TextInput(attrs={
            'inputmode': 'numeric',
            'pattern': '[0-9]{9}',
            'maxlength': '9',
            'placeholder': '991234567',
            'autocomplete': 'tel-national',
        }),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'username', 'first_name', 'last_name',
            'email', 'phone_number', 'role',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Create Account'))
        self.fields['username'].widget.attrs.setdefault('autofocus', True)
        self.fields['username'].widget.attrs.setdefault('autocomplete', 'username')
        self.fields['email'].widget.attrs.setdefault('autocomplete', 'email')
        self.fields['first_name'].widget.attrs.setdefault('autocomplete', 'given-name')
        self.fields['last_name'].widget.attrs.setdefault('autocomplete', 'family-name')

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with that email already exists.')
        return email

    def clean_phone_number(self):
        """Normalise '+265 991 234 567' / '991234567' → '+265991234567'."""
        raw = self.cleaned_data.get('phone_number', '')
        if not raw:
            return ''
        digits = ''.join(c for c in raw if c.isdigit())
        if digits.startswith('265'):
            digits = digits[3:]
        digits = digits[-9:]
        if len(digits) != 9:
            raise forms.ValidationError('Phone must be 9 digits after +265.')
        normalised = f'+265{digits}'
        _MALAWI_PHONE_VALIDATOR(normalised)
        return normalised


# ---------------------------------------------------------------------------
# Admin user management
# ---------------------------------------------------------------------------
class UserCreateForm(UserCreationForm):
    """AC-01: admin-created accounts for any role."""
    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'username', 'first_name', 'last_name',
            'email', 'role', 'phone_number',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Create User'))

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with that email already exists.')
        return email


class UserUpdateForm(UserChangeForm):
    """AC-22: admin can view/edit any user's profile including role."""
    password = None

    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name', 'email',
            'role', 'phone_number', 'profile_picture',
            'is_active',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        enable_dropzone(self)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Changes'))

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            return email
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Another account already uses that email.')
        return email

    def clean_phone_number(self):
        raw = (self.cleaned_data.get('phone_number') or '').strip()
        if not raw:
            return ''
        digits = ''.join(c for c in raw if c.isdigit())
        if digits.startswith('265'):
            digits = digits[3:]
        digits = digits[-9:]
        if len(digits) != 9:
            raise forms.ValidationError('Enter 9 digits, e.g. 991234567 or +265 991 234 567.')
        return f'+265{digits}'


# ---------------------------------------------------------------------------
# Self-service profile
# ---------------------------------------------------------------------------
class ProfileForm(forms.ModelForm):
    """
    AC-21: users can edit their own basic profile fields (not role).
    Phone is stored canonically as +265XXXXXXXXX regardless of input format.
    Email collisions with other accounts are rejected.
    """
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'email',
            'phone_number', 'profile_picture', 'preferred_language',
        )
        widgets = {
            'first_name': forms.TextInput(attrs={'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'autocomplete': 'family-name'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email', 'inputmode': 'email'}),
            'phone_number': forms.TextInput(attrs={
                'autocomplete': 'tel',
                'inputmode': 'tel',
                'placeholder': '+265991234567',
            }),
            'preferred_language': forms.Select(choices=[
                ('en', 'English'),
                ('ny', 'Chichewa'),
            ]),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        enable_dropzone(self)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_tag = False   # templates render <form> themselves
        self.helper.add_input(Submit('submit', 'Save Profile'))

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            return email
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Another account already uses that email.')
        return email

    def clean_phone_number(self):
        raw = (self.cleaned_data.get('phone_number') or '').strip()
        if not raw:
            return ''
        digits = ''.join(c for c in raw if c.isdigit())
        if digits.startswith('265'):
            digits = digits[3:]
        digits = digits[-9:]
        if len(digits) != 9:
            raise forms.ValidationError('Enter 9 digits, e.g. 991234567 or +265 991 234 567.')
        return f'+265{digits}'