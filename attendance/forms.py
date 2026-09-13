from django import forms


class AttendanceFilterForm(forms.Form):
    class_name = forms.CharField(required=False)
    stream = forms.ChoiceField(choices=[('', 'All'), ('A', 'A'), ('B', 'B')], required=False)
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
