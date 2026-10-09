"""Forms for the teachers app.

Three forms:

  * ``TeacherForm``            — admin/HR create + edit. Includes the TCM
                                 registration block and the structured
                                 qualification/grade fields added in the
                                 models pass. Cross-field invariants are
                                 enforced by ``Teacher.clean()`` (which
                                 ModelForm calls via ``_post_clean()``)
                                 so they apply to every code path — the
                                 admin's auto-generated form, this form,
                                 and any service-layer caller that goes
                                 through ``full_clean()``. The form adds
                                 only the UX-level nudges that the model
                                 can't express.

  * ``TeacherSelfServiceForm`` — teacher's own profile. Deliberately narrow:
                                 contact details and photo only. Anything
                                 that has regulatory weight (TCM number,
                                 status, license expiry, government grade)
                                 is HR-controlled.

  * ``TCMLicenseRenewalForm``  — HR records a renewal. Updating the
                                 teacher's ``tcm_license_expiry`` and
                                 ``tcm_status`` on the back of a renewal is
                                 a service-layer concern; this form just
                                 captures the receipt. The view that wires
                                 it up is a follow-up.

Business rule: **the form does not require a TCM number to save a teacher.**
An unregistered teacher record is a legitimate state (just hired, licence
pending). The gate that says "cannot be assigned to a class without a
valid TCM license" lives in the class-assignment path, not here.

Error-message ownership:
  * "Registered/Provisional needs a TCM number"
  * Grade/level mismatch (PT4–PT1 vs TI/TJ)
  * Grade on a non-government post
    ... all live in ``Teacher.clean()`` and surface on the form
    automatically via ``ModelForm._post_clean()``. Do NOT also add them
    here, or each message renders twice on the same field.
  * The past-expiry-with-'registered'-status nudge is form-only: it is a
    UX hint steering the user toward the 'Expired' status, not a
    storable-state contradiction — a past expiry on an 'Expired' status
    row is exactly the state the form is trying to reach.
"""
import datetime

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from accounts.models import malawi_phone_validator
from common.forms import enable_dropzone
from .models import Teacher, TCMLicenseRenewal


# ---------------------------------------------------------------------------
# Admin / HR form
# ---------------------------------------------------------------------------
class TeacherForm(forms.ModelForm):
    """Create or edit a teacher.

    Field order below drives rendered order (crispy renders in
    ``Meta.fields`` order). Legacy fields — ``subject``, ``subjects``,
    ``qualification`` — are kept so existing templates, filters and admin
    lists keep working. New structured fields sit alongside them and should
    be preferred going forward.
    """

    class Meta:
        model = Teacher
        fields = [
            # Identity
            'full_name', 'photo', 'gender', 'date_of_birth', 'national_id',
            # Contact
            'phone_number', 'email', 'address',
            # Legacy specialisation (kept — do not remove without updating
            # teacher_list.html, teacher_detail.html, filters.py, admin.py)
            'subject', 'subjects', 'qualification',
            # TCM registration
            'tcm_registration_number', 'tcm_status', 'tcm_license_expiry',
            # Academic qualifications
            'highest_academic_qualification', 'academic_institution',
            # Professional qualifications
            'professional_qualification', 'professional_institution',
            'year_qualified',
            # Teaching level + grade
            'teaching_level', 'government_grade',
            # Employment
            'employment_type',
            # Lifecycle
            'status',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'tcm_license_expiry': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }
        help_texts = {
            'subject': 'Free-text specialisation shown on lists and reports. '
                       'Prefer the structured fields below for new records.',
            'qualification': 'Free-text summary. Prefer the structured '
                             'academic/professional fields below.',
            'government_grade': 'Public-service posts only. Leave blank for '
                                'private, church and volunteer roles.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        enable_dropzone(self)

        # Unique-but-nullable columns must not be forced in the form — a
        # legacy row migrating in with no national_id should still be
        # editable without inventing one.
        self.fields['national_id'].required = False
        self.fields['tcm_registration_number'].required = False

        # Render any empty-string-as-choice situations as real empties.
        self.fields['government_grade'].required = False
        self.fields['employment_type'].required = False

        # The model-level validator would also run, but attaching it here
        # makes the error render on the field rather than as non-field.
        self.fields['phone_number'].validators.append(malawi_phone_validator)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_tag = True
        self.helper.add_input(Submit('submit', 'Save Teacher'))
        self.helper.attrs = {'enctype': 'multipart/form-data'}

    # -- Field-level --------------------------------------------------------

    def clean_national_id(self):
        """Return ``None`` for blank input so SQL's "NULLs are distinct"
        rule applies under the UNIQUE constraint.

        (A blank CharField normally round-trips as '', and two rows with
        '' would collide on Postgres.)
        """
        value = (self.cleaned_data.get('national_id') or '').strip()
        if not value:
            return None
        qs = Teacher.objects.filter(national_id__iexact=value)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                'Another teacher already has that national ID.'
            )
        return value

    def clean_tcm_registration_number(self):
        """Same blank-to-None treatment as ``national_id``, plus a
        uniqueness check that surfaces on the field."""
        value = (self.cleaned_data.get('tcm_registration_number') or '').strip()
        if not value:
            return None
        qs = Teacher.objects.filter(tcm_registration_number__iexact=value)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                'Another teacher already has that TCM registration number.'
            )
        return value

    def clean_year_qualified(self):
        year = self.cleaned_data.get('year_qualified')
        if year is None:
            return year
        current = datetime.date.today().year
        if year < 1960 or year > current:
            raise forms.ValidationError(
                f'Year qualified must be between 1960 and {current}.'
            )
        return year

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob is None:
            return dob
        today = datetime.date.today()
        if dob > today:
            raise forms.ValidationError('Date of birth cannot be in the future.')
        age = today.year - dob.year - (
            (today.month, today.day) < (dob.month, dob.day)
        )
        if age < 16:
            raise forms.ValidationError(
                'A teacher must be at least 16 years old.'
            )
        return dob

    # -- Cross-field --------------------------------------------------------

    def clean(self):
        cleaned = super().clean()

        tcm_status = cleaned.get('tcm_status')
        tcm_expiry = cleaned.get('tcm_license_expiry')

        # Grade/level, grade/employment-type and the "Registered/Provisional
        # requires a number" rule all live in Teacher.clean() and surface
        # here automatically via ModelForm._post_clean() — deliberately not
        # duplicated, or each message would render twice on the same field.

        # TCM: a live status with a past expiry is a *stale* record — the
        # right answer is to flip status to 'Expired', not to save as-is.
        # This one stays form-only: it is a UX nudge, not a storable-state
        # contradiction (a past expiry is a perfectly legal value on an
        # 'Expired' status row, which is exactly the state the form is
        # trying to steer the user toward).
        if (
            tcm_status == Teacher.TCMStatus.REGISTERED
            and tcm_expiry
            and tcm_expiry < datetime.date.today()
        ):
            self.add_error(
                'tcm_status',
                'This license expired on '
                f'{tcm_expiry:%d %b %Y}. Set the status to "Expired" before '
                'saving, or update the expiry date if it has been renewed.',
            )

        # Informational: an unqualified teacher is a warning, not an error.
        # The template should surface this (banner / badge) rather than
        # blocking the save — the ISAMA policy allows MSCE + experience in
        # private schools.
        # (No self.add_error here on purpose.)

        return cleaned


# ---------------------------------------------------------------------------
# Teacher self-service
# ---------------------------------------------------------------------------
class TeacherSelfServiceForm(forms.ModelForm):
    """TC-30/31: teachers edit their own contact details.

    Regulatory fields (TCM number, status, license expiry, government
    grade, employment type) are intentionally not editable here — those
    are HR-controlled. A teacher renewing their licence uploads a
    certificate scan through the renewal form (or, later, a self-service
    'renew license' submission), and HR confirms the record change.
    """

    class Meta:
        model = Teacher
        fields = ['phone_number', 'email', 'address', 'photo']
        widgets = {'address': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        enable_dropzone(self)
        self.fields['phone_number'].validators.append(malawi_phone_validator)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_tag = True
        self.helper.add_input(Submit('submit', 'Save Changes'))
        self.helper.attrs = {'enctype': 'multipart/form-data'}


# ---------------------------------------------------------------------------
# TCM renewal (HR)
# ---------------------------------------------------------------------------
class TCMLicenseRenewalForm(forms.ModelForm):
    """Record a TCM license renewal.

    Captures the receipt side of a renewal. Roll-up of the teacher's
    ``tcm_license_expiry`` (and flipping ``tcm_status`` back to
    ``registered``) is a service-layer concern — the view that uses this
    form should, after a successful save, set::

        teacher.tcm_license_expiry = renewal.expires_at
        teacher.tcm_status = Teacher.TCMStatus.REGISTERED
        teacher.save(update_fields=['tcm_license_expiry', 'tcm_status'])

    Do that in a transaction; a renewal row whose teacher record was not
    updated is a silent compliance bug.
    """

    class Meta:
        model = TCMLicenseRenewal
        fields = [
            'renewed_at', 'expires_at',
            'receipt_number', 'renewal_fee_paid', 'document',
        ]
        widgets = {
            'renewed_at': forms.DateInput(attrs={'type': 'date'}),
            'expires_at': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        enable_dropzone(self)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_tag = True
        self.helper.add_input(Submit('submit', 'Record Renewal'))
        self.helper.attrs = {'enctype': 'multipart/form-data'}

    def clean(self):
        cleaned = super().clean()
        renewed = cleaned.get('renewed_at')
        expires = cleaned.get('expires_at')

        if renewed and expires and expires <= renewed:
            self.add_error(
                'expires_at',
                'The new expiry date must be after the renewal date.',
            )

        # A renewal that expires today is useless — the teacher would be
        # immediately in breach. Require a future date on creation.
        if expires and expires <= datetime.date.today() and not self.instance.pk:
            self.add_error(
                'expires_at',
                'A new renewal must expire in the future.',
            )

        return cleaned