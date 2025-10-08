from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile, Company

class BusinessOwnerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email'
    }))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your first name'
    }))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your last name'
    }))
    
    # Company selection
    company_choice = forms.ChoiceField(
        choices=[('new', 'Create New Company'), ('existing', 'Select Existing Company')],
        widget=forms.RadioSelect(attrs={'class': 'company-choice'}),
        initial='new'
    )
    existing_company = forms.ModelChoiceField(
        queryset=Company.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select a company"
    )
    new_company_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter company name'
        })
    )
    company_address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Enter company address',
            'rows': 3
        })
    )
    company_contact = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter contact information'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['company_choice'] and hasattr(field, 'widget') and hasattr(field.widget, 'attrs'):
                if field_name in ['existing_company', 'new_company_name', 'company_address', 'company_contact']:
                    field.widget.attrs.update({'class': 'form-control company-field'})
                else:
                    field.widget.attrs.update({'class': 'form-control'})
            
            if field_name == 'username':
                field.widget.attrs.update({'placeholder': 'Choose a username'})
            elif field_name == 'password1':
                field.widget.attrs.update({'placeholder': 'Enter password'})
            elif field_name == 'password2':
                field.widget.attrs.update({'placeholder': 'Confirm password'})

    def clean(self):
        cleaned_data = super().clean()
        company_choice = cleaned_data.get('company_choice')
        
        if company_choice == 'new':
            if not cleaned_data.get('new_company_name'):
                self.add_error('new_company_name', 'Company name is required when creating a new company.')
        else:  # existing
            if not cleaned_data.get('existing_company'):
                self.add_error('existing_company', 'Please select an existing company.')
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            
            # Handle company creation/selection
            company_choice = self.cleaned_data['company_choice']
            if company_choice == 'new':
                company = Company.objects.create(
                    name=self.cleaned_data['new_company_name'],
                    address=self.cleaned_data['company_address'],
                    contact_info=self.cleaned_data['company_contact']
                )
            else:
                company = self.cleaned_data['existing_company']
            
            # Create user profile
            UserProfile.objects.create(
                user=user,
                role='business_owner',
                company=company
            )
        return user

class StaffRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email'
    }))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your first name'
    }))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your last name'
    }))
    company = forms.ModelChoiceField(
        queryset=Company.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select your company"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field, 'widget') and hasattr(field.widget, 'attrs'):
                field.widget.attrs.update({'class': 'form-control'})
            
            if field_name == 'username':
                field.widget.attrs.update({'placeholder': 'Choose a username'})
            elif field_name == 'password1':
                field.widget.attrs.update({'placeholder': 'Enter password'})
            elif field_name == 'password2':
                field.widget.attrs.update({'placeholder': 'Confirm password'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                role='staff',
                company=self.cleaned_data['company']
            )
        return user

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })