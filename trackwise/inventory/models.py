from django.db import models
from django.urls import reverse
from accounts.models import Company

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
    image = models.ImageField(upload_to='products/', blank=True, null=True)
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
        return f"{self.quantity} {self.get_unit_of_measure_display()}"
    
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