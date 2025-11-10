from django import forms
from .models import ReportConfiguration

class ReportFilterForm(forms.Form):
    DATE_RANGE_CHOICES = [
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('this_week', 'This Week'),
        ('last_week', 'Last Week'),
        ('this_month', 'This Month'),
        ('last_month', 'Last Month'),
        ('custom', 'Custom Date Range'),
    ]
    
    date_range = forms.ChoiceField(choices=DATE_RANGE_CHOICES, required=True)
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    staff_member = forms.ChoiceField(required=False, choices=[])
    
    def __init__(self, *args, **kwargs):
        staff_choices = kwargs.pop('staff_choices', [])
        super().__init__(*args, **kwargs)
        self.fields['staff_member'].choices = staff_choices

class ExportFormatForm(forms.Form):
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
    ]
    
    export_format = forms.ChoiceField(choices=FORMAT_CHOICES, required=True)
    include_charts = forms.BooleanField(required=False, initial=True)