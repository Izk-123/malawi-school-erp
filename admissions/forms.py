from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from accounts.models import User
from common.forms import enable_dropzone
from .models import (
    Applicant, ApplicantPriority, DocumentAttachment, Enquiry,
    EntranceExam, ExamAssignment, ExamMark, Interview, Offer,
)


def _helper(text='Save'):
    h = FormHelper()
    h.form_method = 'post'
    h.add_input(Submit('submit', text))
    return h


class EnquiryForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = [
            'source', 'enquiry_date', 'parent_name', 'guardian_phone',
            'guardian_email', 'student_name', 'current_class',
            'applying_for', 'boarding_preference', 'notes', 'follow_up_due',
        ]
        widgets = {
            'enquiry_date': forms.DateInput(attrs={'type': 'date'}),
            'follow_up_due': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = _helper('Save Enquiry')


class ApplicantForm(forms.ModelForm):
    class Meta:
        model = Applicant
        fields = [
            'full_name', 'gender', 'date_of_birth', 'national_id', 'photo',
            'address', 'guardian_name', 'guardian_phone', 'guardian_email',
            'guardian_relationship', 'guardian_national_id',
            'previous_school', 'prior_academic_score', 'pslce_number',
            'applying_for', 'boarding_preference',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        enable_dropzone(self)
        self.helper = _helper('Save Applicant')
        self.helper.attrs = {'enctype': 'multipart/form-data'}


class DocumentAttachmentForm(forms.ModelForm):
    class Meta:
        model = DocumentAttachment
        fields = ['document_type', 'file']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = _helper('Upload Document')


class PriorityFlagForm(forms.ModelForm):
    class Meta:
        model = ApplicantPriority
        fields = ['flag_type', 'bonus_points', 'reason']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = _helper('Add Priority Flag')


class EntranceExamForm(forms.ModelForm):
    class Meta:
        model = EntranceExam
        fields = [
            'name', 'exam_date', 'start_time', 'end_time',
            'venue', 'capacity', 'cutoff_score', 'notes',
        ]
        widgets = {
            'exam_date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = _helper('Save Session')


class ExamAssignmentForm(forms.ModelForm):
    class Meta:
        model = ExamAssignment
        fields = ['applicant', 'seat_number']

    def __init__(self, *args, **kwargs):
        session = kwargs.pop('session', None)
        super().__init__(*args, **kwargs)
        if session:
            self.instance.session = session
            already = session.assignments.values_list('applicant_id', flat=True)
            self.fields['applicant'].queryset = Applicant.objects.exclude(id__in=already)
        self.fields['seat_number'].required = False
        self.helper = _helper('Assign to Session')


class ExamMarkForm(forms.ModelForm):
    class Meta:
        model = ExamMark
        fields = ['subject', 'score']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = _helper('Save Mark')


class InterviewForm(forms.ModelForm):
    class Meta:
        model = Interview
        fields = [
            'scheduled_for', 'location', 'interviewer',
            'student_score', 'parent_score', 'notes', 'recommendation',
        ]
        widgets = {
            'scheduled_for': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M',
            ),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.scheduled_for:
            self.initial['scheduled_for'] = self.instance.scheduled_for.strftime('%Y-%m-%dT%H:%M')
        self.helper = _helper('Save Interview')


class OfferIssueForm(forms.Form):
    """Only Head Teacher / Deputy / Admin reach this form (AD-27)."""
    deadline_days = forms.IntegerField(
        min_value=1, max_value=60, initial=14,
        help_text='Days the applicant has to accept (1-60).',
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}), required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = _helper('Issue Offer')


class AdmitForm(forms.Form):
    """AD-40: the human-entered part of admission."""
    class_name = forms.CharField(max_length=10, initial='Form 1')
    stream = forms.ChoiceField(choices=[('A', 'A'), ('B', 'B'), ('C', 'C')])
    boarding_status = forms.ChoiceField(
        choices=[('day', 'Day scholar'), ('boarder', 'Boarder')],
        initial='day',
    )
    hostel = forms.CharField(max_length=100, required=False)
    bed_number = forms.CharField(max_length=10, required=False)
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}), required=False,
        help_text='AD-59: recorded on the applicant and the audit log.',
    )

    def __init__(self, *args, **kwargs):
        applicant = kwargs.pop('applicant', None)
        super().__init__(*args, **kwargs)
        if applicant:
            self.fields['class_name'].initial = applicant.applying_for
            self.fields['boarding_status'].initial = applicant.boarding_preference
        self.helper = _helper('Confirm Admission')

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('boarding_status') == 'boarder' and not cleaned.get('hostel'):
            self.add_error('hostel', 'A hostel is required for a boarder.')
        return cleaned