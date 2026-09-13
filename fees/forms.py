from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import FeeTransaction


class RecordPaymentForm(forms.ModelForm):
    class Meta:
        model = FeeTransaction
        fields = ['student', 'amount', 'method', 'date']
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        student_qs = kwargs.pop('student_queryset', None)
        super().__init__(*args, **kwargs)
        if student_qs is not None:
            self.fields['student'].queryset = student_qs
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Record Payment'))

    def clean(self):
        cleaned = super().clean()
        student = cleaned.get('student')
        amount = cleaned.get('amount')
        if student and amount and amount > student.balance:
            raise forms.ValidationError(
                f'Amount exceeds outstanding balance (MK {student.balance:,.2f}).'
            )
        return cleaned
