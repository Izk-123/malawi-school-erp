from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Row, Column
from .models import Student, GuardianContact
from common.forms import enable_dropzone


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'full_name', 'gender', 'date_of_birth', 'photo',
            'guardian_name', 'guardian_phone', 'guardians', 'address',
            'class_name', 'stream', 'status', 'fees_total', 'fees_paid',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }
        help_texts = {
            'guardian_phone': 'Format: +265991234567 (spaces allowed)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        enable_dropzone(self)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Student'))
        self.helper.attrs = {'enctype': 'multipart/form-data'}


class GuardianContactForm(forms.ModelForm):
    class Meta:
        model = GuardianContact
        fields = ['name', 'phone_number', 'relationship', 'is_primary', 'linked_user']
        help_texts = {'phone_number': 'Format: +265991234567 (spaces allowed)'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Contact'))


class PromoteStudentsForm(forms.Form):
    """ST-12: bulk-promote every student in a class/stream to the next class."""
    class_name = forms.CharField(label='From Class')
    stream = forms.ChoiceField(choices=[('A', 'A'), ('B', 'B')])
    new_class_name = forms.CharField(label='To Class')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Promote Students'))
