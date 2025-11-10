from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from accounts.models import UserProfile
from .models import StaffProfile

class StaffUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address'
        })
    )
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name'
        })
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name'
        })
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm password'})

class StaffProfileForm(forms.ModelForm):
    hire_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    assigned_locations = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Enter assigned locations (comma-separated)'
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'form-control',
            'placeholder': 'Enter any additional notes...'
        })
    )
    
    class Meta:
        model = StaffProfile
        fields = ['employee_id', 'position', 'department', 'hire_date', 'salary', 'status', 'assigned_locations', 'permissions', 'notes']
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter employee ID'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter position'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter department'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter salary', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'permissions': forms.HiddenInput(),  # We'll handle this via JavaScript
        }
    
    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id')
        if StaffProfile.objects.filter(employee_id=employee_id).exists():
            if not self.instance or self.instance.employee_id != employee_id:
                raise ValidationError('An employee with this ID already exists.')
        return employee_id

class StaffSearchForm(forms.Form):
    search_query = forms.CharField(
        required=False, 
        max_length=100, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, email, or employee ID...'
        })
    )
    department = forms.CharField(
        required=False, 
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by department...'
        })
    )
    status = forms.ChoiceField(
        required=False, 
        choices=[('', 'All Status')] + StaffProfile.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class StaffUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = StaffProfile
        fields = ['employee_id', 'position', 'department', 'hire_date', 'salary', 'status', 'assigned_locations', 'notes']
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'hire_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'assigned_locations': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }