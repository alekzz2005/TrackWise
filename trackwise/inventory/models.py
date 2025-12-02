from django.db import models
from django.urls import reverse
from accounts.models import Company
import base64

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('electronics', 'Electronics'),
        ('clothing', 'Clothing'),
        ('food', 'Food & Beverages'),
        ('books', 'Books'),
        ('home', 'Home & Garden'),
        ('sports', 'Sports & Outdoors'),
        ('health', 'Health & Beauty'),
        ('other', 'Other'),
    ]

    UNIT_CHOICES = [
        ('pieces', 'Pieces'),
        ('packs', 'Packs'),
        ('boxes', 'Boxes'),
        ('kilograms', 'Kilograms'),
        ('grams', 'Grams'),
        ('liters', 'Liters'),
        ('meters', 'Meters'),
        ('units', 'Units'),
        ('pairs', 'Pairs'),
        ('sets', 'Sets'),
        ('bottles', 'Bottles'),
        ('cartons', 'Cartons'),
        ('bags', 'Bags'),
    ]
    
    item_name = models.CharField(max_length=200)
    
    # Store base64 encoded image as TextField
    image = models.TextField(null=True, blank=True)
    image_content_type = models.CharField(max_length=50, null=True, blank=True)
    image_name = models.CharField(max_length=255, null=True, blank=True)
    
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    quantity = models.IntegerField(default=0)
    unit_of_measure = models.CharField(max_length=20, choices=UNIT_CHOICES, default='pieces')
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.item_name} ({self.company.name})"
    
    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'pk': self.pk})
    
    @property
    def total_value(self):
        return self.quantity * self.cost_price
    
    def get_display_quantity(self):
        return f"{self.quantity} {self.unit_of_measure}"
    
    @property
    def singular_unit(self):
        """Return the singular version of the unit of measure (e.g., 'Liters' → 'Liter')."""
        unit = self.get_unit_of_measure_display()
        exceptions = {
            "Boxes": "Box",
            "Pairs": "Pair",
            "Bottles": "Bottle",
            "Cartons": "Carton",
            "Bags": "Bag",
            "Sets": "Set",
            "Packs": "Pack",
            "Pieces": "Piece",
            "Kilograms": "Kilogram",
            "Grams": "Gram",
            "Liters": "Liter",
            "Meters": "Meter",
            "Units": "Unit",
        }
        return exceptions.get(unit, unit[:-1] if unit.endswith("s") else unit)
    
    @property
    def image_base64(self):
        """Get image as base64 data URL for HTML display."""
        if self.image:
            try:
                # Remove any existing data URL prefix if present
                image_data = self.image
                if image_data.startswith('data:'):
                    # Extract just the base64 part
                    parts = image_data.split(',', 1)
                    if len(parts) > 1:
                        image_data = parts[1]
                
                return f"data:{self.image_content_type or 'image/jpeg'};base64,{image_data}"
            except Exception as e:
                print(f"Error in image_base64: {e}")
                return None
        return None
    
    def set_image_from_file(self, uploaded_file):
        """Set image from uploaded file."""
        if uploaded_file:
            try:
                # Read file content
                file_content = uploaded_file.read()
                
                # Encode to base64
                encoded = base64.b64encode(file_content).decode('utf-8')
                
                # Store in image field
                self.image = encoded
                self.image_content_type = uploaded_file.content_type
                self.image_name = uploaded_file.name
                return True
            except Exception as e:
                print(f"Error setting image: {e}")
                return False
        return False