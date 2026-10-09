"""Forms for the accounts app.

Notes:
  - SchoolLoginForm: username *or* email, no role dropdown (AC-07a).
  - ParentSelfRegistrationForm: governance doc §3 — parents only, and only
    with a verified link to an existing student (student ID + admission
    code + guardian phone on file). Students/teachers/staff never
    self-register.
  - InvitationClaimForm: sets the password on an account created by
    invitation; used by ClaimInvitationView.
  - UserCreateForm/UserUpdateForm: admin-only, any role.
  - ProfileForm: self-service, role cannot be changed here.
  - ApprovalRequestForm / ApprovalDecisionForm: HR drafts, Head Teacher
    decides (doc §5, two-step workflow).
"""
from django import forms
from django.contrib.auth.forms import (
    UserCreationForm,
    UserChangeForm,
    AuthenticationForm,
    SetPasswordForm,
)
from django.core.validators import RegexValidator
import re
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from common.forms import enable_dropzone
from students.models import Student
from .models import User, ApprovalRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _normalise_malawi_phone(raw: str) -> str:
    """Turn '991234567' or '+265 991 234 567' into '+265991234567'.
    Returns '' if it can't be normalised to 9 digits after +265."""
    digits = ''.join(c for c in (raw or '') if c.isdigit())
    if digits.startswith('265'):
        digits = digits[3:]
    digits = digits[-9:]
    if len(digits) != 9:
        return ''
    return f'+265{digits}'


_MALAWI_PHONE_VALIDATOR = RegexValidator(
    r'^\+265\d{9}$',
    'Enter a valid Malawian number (9 digits after +265).',
)


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
# Parent self-registration (doc §3)
# ---------------------------------------------------------------------------
class ParentSelfRegistrationForm(UserCreationForm):
    """Governance doc §3: only Parents may self-register, and only with a
    verified link to an existing student (student ID + admission code +
    guardian phone on file).

    The old form allowed Student signup too — that's removed, because
    students are minors and their accounts are created by the Registry
    Clerk on admission.
    """
    student_id = forms.CharField(
        label='Student ID',
        max_length=15,
        help_text='Found on the admission letter, e.g. STU-2025-001.',
        widget=forms.TextInput(attrs={'autocomplete': 'off'}),
    )
    admission_code = forms.CharField(
        label='Admission code',
        max_length=12,
        help_text='The one-time code on the admission letter.',
        widget=forms.TextInput(attrs={'autocomplete': 'off'}),
    )
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(
        required=True,
        help_text='Must match the guardian phone number on file.',
        widget=forms.TextInput(attrs={
            'inputmode': 'numeric',
            'maxlength': '9',
            'placeholder': '991234567',
            'autocomplete': 'tel-national',
        }),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Create Parent Account'))
        self.fields['username'].widget.attrs.setdefault('autofocus', True)
        self.fields['username'].widget.attrs.setdefault('autocomplete', 'username')
        self.fields['email'].widget.attrs.setdefault('autocomplete', 'email')
        self.fields['first_name'].widget.attrs.setdefault('autocomplete', 'given-name')
        self.fields['last_name'].widget.attrs.setdefault('autocomplete', 'family-name')
        # Populated by clean() once the student + code check passes.
        self.student = None

    def clean(self):
        cleaned = super().clean()

        student_id = (cleaned.get('student_id') or '').strip().upper()
        code = (cleaned.get('admission_code') or '').strip().upper()
        phone_raw = cleaned.get('phone_number') or ''

        if not student_id:
            self.add_error('student_id', 'Student ID is required.')
            return cleaned
        if not code:
            self.add_error('admission_code', 'Admission code is required.')
            return cleaned

        student = Student.objects.filter(student_id__iexact=student_id).first()
        if not student:
            self.add_error('student_id', 'No student found with that ID.')
            return cleaned

        # Admission code check — the Student model gains an `admission_code`
        # field defaulting to a random 8-char code on creation.
        if (getattr(student, 'admission_code', '') or '').upper() != code:
            self.add_error('admission_code', 'That admission code is incorrect.')
            return cleaned

        # Guardian phone must be on file for the student (either the main
        # guardian_phone field or one of the GuardianContact rows).
        normalised = _normalise_malawi_phone(phone_raw)
        if not normalised:
            self.add_error('phone_number', 'Enter a valid Malawian mobile number (9 digits).')
            return cleaned

        phone_matches = (
            normalised == (student.guardian_phone or '')
            or student.guardian_contacts.filter(phone_number=normalised).exists()
        )
        if not phone_matches:
            self.add_error(
                'phone_number',
                "This number isn't on file as a guardian for that student.",
            )
            return cleaned

        self.student = student
        return cleaned

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with that email already exists.')
        return email


# ---------------------------------------------------------------------------
# Invitation claim (doc §4)
# ---------------------------------------------------------------------------
class InvitationClaimForm(SetPasswordForm):
    """Sets the password on an account whose record was created by the
    school. Uses Django's SetPasswordForm so AC-13/15 validators apply."""
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Set Password & Continue'))


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
            'is_active', 'two_factor_enabled',
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
        normalised = _normalise_malawi_phone(raw)
        if not normalised:
            raise forms.ValidationError('Enter 9 digits, e.g. 991234567 or +265 991 234 567.')
        return normalised


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
        normalised = _normalise_malawi_phone(raw)
        if not normalised:
            raise forms.ValidationError('Enter 9 digits, e.g. 991234567 or +265 991 234 567.')
        return normalised


# ---------------------------------------------------------------------------
# Approval workflow (doc §5 — HR drafts, Head Teacher decides)
# ---------------------------------------------------------------------------
class ApprovalRequestForm(forms.ModelForm):
    """HR Officer draft for a teacher / non-teaching staff account."""

    class Meta:
        model = ApprovalRequest
        fields = [
            'purpose',
            'proposed_username', 'proposed_first_name', 'proposed_last_name',
            'proposed_email', 'proposed_phone',
            'teacher_record', 'staff_record',
            'reason',
        ]
        widgets = {
            'proposed_phone': forms.TextInput(attrs={
                'inputmode': 'numeric', 'placeholder': '+265991234567',
            }),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher_record'].required = False
        self.fields['staff_record'].required = False
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit for Approval'))

    def clean_proposed_phone(self):
        raw = (self.cleaned_data.get('proposed_phone') or '').strip()
        if not raw:
            raise forms.ValidationError('Phone number is required.')
        normalised = _normalise_malawi_phone(raw)
        if not normalised:
            raise forms.ValidationError('Enter 9 digits, e.g. 991234567 or +265 991 234 567.')
        return normalised

    def clean(self):
        cleaned = super().clean()
        purpose = cleaned.get('purpose')
        teacher = cleaned.get('teacher_record')
        staff = cleaned.get('staff_record')

        if purpose == ApprovalRequest.Purpose.TEACHER and not teacher:
            self.add_error('teacher_record', 'A teacher record is required for a teacher account.')
        if purpose == ApprovalRequest.Purpose.STAFF and not staff:
            self.add_error('staff_record', 'A staff record is required for a non-teaching staff account.')

        username = (cleaned.get('proposed_username') or '').strip()
        if username and User.objects.filter(username__iexact=username).exists():
            self.add_error('proposed_username', 'That username is already taken.')

        return cleaned


class ApprovalDecisionForm(forms.Form):
    """Head Teacher records an approve/reject decision on a draft request."""
    decision = forms.ChoiceField(
        choices=[('approve', 'Approve'), ('reject', 'Reject')],
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text='Visible in the audit log and to the drafting HR Officer.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Record Decision'))
        
# ---------------------------------------------------------------------------
# Admission-code claim entry (parent journey doc Stage 8)
# ---------------------------------------------------------------------------
class ClaimByCodeForm(forms.Form):
    """Entry point for a parent who can't tap the invitation link — the
    fallback the offer letter prints as 'Or use code: K7X3-MN9F'.

    Takes the admission code from the letter plus the guardian phone on
    file, and hands off to the normal ClaimInvitationView. Deliberately
    does NOT ask for a password here: password entry stays in one place
    (InvitationClaimForm) so the validators and audit logging only run
    once.
    """
    admission_code = forms.CharField(
        max_length=12,
        label='Admission code',
        widget=forms.TextInput(attrs={
            'autocomplete': 'off',
            'autocapitalize': 'characters',
            'autocorrect': 'off',
            'spellcheck': 'false',
            'placeholder': 'e.g. K7X3MN9F',
            'inputmode': 'text',
        }),
        help_text='The 8-character code printed on the admission letter.',
    )
    phone_number = forms.CharField(
        max_length=13,
        label='Guardian phone number',
        widget=forms.TextInput(attrs={
            'inputmode': 'numeric',
            'pattern': '[0-9]{9}',
            'maxlength': '9',
            'placeholder': '991234567',
            'autocomplete': 'tel-national',
        }),
        help_text='The number on file with the school.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Continue'))

    def clean_admission_code(self):
        raw = (self.cleaned_data.get('admission_code') or '').strip().upper()
        # Accept the printed hyphenated form (K7X3-MN9F) and any surrounding
        # whitespace, then normalise to the storage form (K7X3MN9F).
        code = re.sub(r'[\s\-]', '', raw)
        if not code:
            raise forms.ValidationError(
                'Enter the admission code from your admission letter.'
            )
        if len(code) < 6:
            raise forms.ValidationError(
                'That code looks too short. It should be 8 characters.'
            )
        return code

    def clean_phone_number(self):
        raw = self.cleaned_data.get('phone_number') or ''
        normalised = _normalise_malawi_phone(raw)
        if not normalised:
            raise forms.ValidationError(
                'Enter a valid Malawian mobile number (9 digits after +265).'
            )
        return normalised