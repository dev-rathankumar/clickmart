from tabnanny import verbose
from django.db import models
from vendor.models import Vendor
class Category(models.Model):
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories'
    )
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    category_name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=250, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def clean(self):
        self.category_name = self.category_name.capitalize()
    
    def __str__(self):
        return self.category_name
    
    def get_subcategory_count(self):
        return self.subcategories.count()

class FoodItem(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='fooditems')
    food_title = models.CharField(max_length=50)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=250, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='foodimages')
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.food_title

class Product(models.Model):

    vendor          = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    product_name    = models.CharField(max_length=200)
    slug            = models.SlugField(max_length=300, unique=True, blank=True)
    description     = models.TextField()
    full_specification = models.TextField(blank=True, default='')
    regular_price   = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price      = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null = True)
    image           = models.ImageField(upload_to='store/products/%Y/%m/%d')
    stock           = models.IntegerField(blank=True, null = True)
    is_available    = models.BooleanField(default=True)
    category        = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(Category, related_name='subcategory_products', on_delete=models.CASCADE)
    is_popular      = models.BooleanField(default=False, blank=True)
    is_active       = models.BooleanField(default=False)
    created_date    = models.DateTimeField(auto_now_add=True)
    modified_date   = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name
    