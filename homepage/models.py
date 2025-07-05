from django.db import models
from vendor.models import Vendor
from django.core.exceptions import ValidationError
from unified.models import Category

class HomePageBanner(models.Model):
    image = models.ImageField(upload_to='cover_page_banners/', help_text="Recommended resolution: 1920x442 pixels. Ensure the image is in landscape orientation for best results.")
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, blank=True, null=True)
    link = models.URLField(blank=True, null=True, help_text="Enter the full URL, including domain (e.g., https://www.example.com).")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, blank=False, null=False)

    class Meta:
        ordering = ['order']  # Important!

    def __str__(self):
        return self.vendor.vendor_name if self.vendor else "No Vendor"

    def clean(self):
        # Custom validation: at least one of vendor or link is required
        if not self.vendor and not self.link:
            raise ValidationError("Either 'vendor' or 'link' must be provided.")

    def save(self, *args, **kwargs):
        self.full_clean()  # Call clean() before saving
        super().save(*args, **kwargs)
    

class CategoryBanner(models.Model):
    image = models.ImageField(upload_to='category_banners/', help_text="Recommended resolution: 768x450 pixels. Ensure the image is in landscape orientation for best results.")
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    link = models.URLField(help_text="Enter the full URL, including domain (e.g., https://www.example.com).")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.category.category_name
    

class ProductCollection(models.Model):
    name = models.CharField(max_length=255, help_text="Enter a collection name that matches the logic (e.g., Lowest Price Guarantee).")
    slug = models.SlugField(unique=True)
    active = models.BooleanField(default=True)
    
    # For now, store the logic type (you can extend this later to include parameters)
    LOGIC_CHOICES = [
        # ('popular', 'Popular Products'),
        ('low_price', 'Lowest Price Guarantee'),
        # ('top_rated', 'Top Rated'),
        ('latest', 'Latest Products'),
        # ('top_collection', 'Flickbasket Top Collection')
    ]
    logic = models.CharField(max_length=50, choices=LOGIC_CHOICES)

    def __str__(self):
        return self.name
