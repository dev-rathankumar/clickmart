from django.db import models
from menu.models import Category
from vendor.models import Vendor
from django.template.defaultfilters import slugify
from inventory.models import tax as TaxCategory
from inventory.models import deposit as DepositCategory


class Product(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='products')
    product_name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    product_desc = models.TextField(blank=True, null=True)
    full_specification = models.TextField(blank=True, default='')
    cost_price = models.DecimalField(max_digits=7, decimal_places=2, default=0, null=False)
    regular_price = models.DecimalField(max_digits=10, decimal_places=2)
    sales_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    image = models.ImageField(upload_to='store/products/%Y/%m/%d')
    is_available = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    subcategory = models.ForeignKey(Category, related_name='subcategory_products', on_delete=models.CASCADE, blank=True, null=True)
    is_popular = models.BooleanField(default=False, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Fields from inventory.product model
    barcode = models.CharField(unique=True, max_length=16, blank=False, null=False)
    qty = models.IntegerField(default=0, null=False)
    tax_category     = models.ForeignKey(TaxCategory, on_delete=models.RESTRICT, null=False,blank=False, related_name='products')
    deposit_category = models.ForeignKey(DepositCategory, on_delete=models.RESTRICT, null=False,blank=False, related_name='products')
    
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.product_name)
        super().save(*args, **kwargs)

    def get_fields(self):
        return [
            ("Barcode", self.barcode),
            ("Name", self.product_name),
            ("Product Description", self.product_desc),
            ("Regular Price", self.regular_price),
            ("Sale Price", self.sales_price),
            ("Stock", self.qty),
            ("Department Category", self.category.category_name),
            ("Tax Category", self.tax_category.tax_category),
            ("Deposit Category", self.deposit_category.deposit_category),
        ]

    def get_fields_2(self):
        return [
            ("Barcode", self.barcode),
            ("Name", self.product_name),
            ("Inventory Qty", self.qty),
            ("Sales Price", self.sales_price),
            ("Cost Price", self.cost_price),
            ("Department Category", self.category.category_name),
            ("Tax Category", self.tax_category.tax_category),
            ("Tax Percentage", self.tax_category.tax_percentage),
            # ("Deposit Category", self.deposit_category.deposit_category),
            # ("Deposit Value", self.deposit_category.deposit_value),
        ]