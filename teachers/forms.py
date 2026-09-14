from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import Teacher
from common.forms import enable_dropzone


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            'full_name', 'photo', 'gender', 'date_of_birth', 'subject', 'subjects',
            'qualification', 'phone_number', 'email', 'address', 'status',
        ]
        widgets = {'date_of_birth': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        enable_dropzone(self)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Teacher'))
        self.helper.attrs = {'enctype': 'multipart/form-data'}


class TeacherSelfServiceForm(forms.ModelForm):
    """TC-30/31: teachers may edit limited fields on their own profile."""
    class Meta:
        model = Teacher
        fields = ['phone_number', 'email', 'address', 'photo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        enable_dropzone(self)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Changes'))
        self.helper.attrs = {'enctype': 'multipart/form-data'}
