from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    # Custom image field - separate from the model's image field
    image_upload = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        label="Upload New Image"
    )
    
    class Meta:
        model = Product
        fields = ['item_name', 'category', 'quantity', 'unit_of_measure', 'cost_price']
        widgets = {
            'item_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter product name'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'unit_of_measure': forms.Select(attrs={
                'class': 'form-control'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter quantity'
            }),
            'cost_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter cost price',
                'step': '0.01'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field, 'widget') and hasattr(field.widget, 'attrs'):
                field.widget.attrs.update({'class': 'form-control'})
    
    def clean_image_upload(self):
        """Clean and validate uploaded image."""
        image = self.cleaned_data.get('image_upload')
        if image:
            # Check if it's a file object (has 'size' attribute)
            if hasattr(image, 'size'):
                # Validate file size (5MB limit)
                if image.size > 5 * 1024 * 1024:
                    raise forms.ValidationError("Image file too large ( > 5MB )")
                
                # Validate file type
                if not image.content_type.startswith('image/'):
                    raise forms.ValidationError("File is not an image")
            else:
                # It's not a file object, likely a string from existing data
                # Don't validate, just return as-is
                pass
        
        return image