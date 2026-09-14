from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import (
    StaffMember, LeaveRequest, StaffTicket, Book, BookLoan, VisitorLog,
    GatePass, SickBayVisit, MedicalRecord, MedicationStock,
)
from common.forms import enable_dropzone


def _helper(text='Save'):
    h = FormHelper()
    h.form_method = 'post'
    h.add_input(Submit('submit', text))
    return h


class StaffMemberForm(forms.ModelForm):
    class Meta:
        model = StaffMember
        fields = ['staff_id', 'full_name', 'position', 'department', 'phone_number', 'email', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = _helper('Save Staff Member')


class StaffProfileForm(forms.ModelForm):
    """STF-03: self-service profile editing - only the fields a staff
    member should be able to change themselves."""
    class Meta:
        model = StaffMember
        fields = ['phone_number', 'address', 'emergency_contact_name', 'emergency_contact_phone', 'next_of_kin']
        widgets = {'address': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = _helper('Save Profile')


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = _helper('Submit Leave Request')

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get('start_date'), cleaned.get('end_date')
        if start and end and end < start:
            raise forms.ValidationError('End date must be on or after the start date.')
        return cleaned


class StaffTicketForm(forms.ModelForm):
    class Meta:
        model = StaffTicket
        fields = ['ticket_type', 'category', 'description', 'photo']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        enable_dropzone(self)
        self.helper = _helper('Submit Report')


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'subject', 'category', 'total_copies']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = _helper('Save Book')


class BookLoanForm(forms.ModelForm):
    class Meta:
        model = BookLoan
        fields = ['book', 'student', 'staff', 'due_date']
        widgets = {'due_date': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].required = False
        self.fields['staff'].required = False
        self.helper = _helper('Issue Book')

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('student') and not cleaned.get('staff'):
            raise forms.ValidationError('Select either a student or a staff borrower.')
        if cleaned.get('student') and cleaned.get('staff'):
            raise forms.ValidationError('Select only one borrower - student OR staff.')
        return cleaned


class VisitorLogForm(forms.ModelForm):
    class Meta:
        model = VisitorLog
        fields = ['name', 'id_number', 'purpose', 'host', 'vehicle_plate']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = _helper('Log Visitor')


class GatePassForm(forms.ModelForm):
    class Meta:
        model = GatePass
        fields = ['student', 'reason']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = _helper('Issue Gate Pass')


class SickBayVisitForm(forms.ModelForm):
    class Meta:
        model = SickBayVisit
        fields = ['student', 'symptoms', 'treatment', 'medicine_dispensed', 'referred', 'referral_notes']
        widgets = {'symptoms': forms.Textarea(attrs={'rows': 2}), 'referral_notes': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = _helper('Record Visit')


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['allergies', 'chronic_conditions', 'immunisation_notes']
        widgets = {f: forms.Textarea(attrs={'rows': 2}) for f in ['allergies', 'chronic_conditions', 'immunisation_notes']}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = _helper('Save Medical Record')


class MedicationStockForm(forms.ModelForm):
    class Meta:
        model = MedicationStock
        fields = ['name', 'quantity', 'reorder_level', 'expiry_date']
        widgets = {'expiry_date': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = _helper('Save Stock Item')
