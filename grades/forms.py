from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import GradeRecord


class GradeRecordForm(forms.ModelForm):
    class Meta:
        model = GradeRecord
        fields = ['student', 'subject', 'syllabus_topic', 'exam', 'score']
        labels = {'syllabus_topic': 'MANEB Topic (optional)'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['syllabus_topic'].required = False
        self.fields['syllabus_topic'].queryset = self.fields['syllabus_topic'].queryset.select_related('subject')
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Grade'))
