from django.db import models
# from menu.models import Category
from vendor.models import Vendor, StoreType
from django.template.defaultfilters import slugify
from inventory.models import tax as TaxCategory
from inventory.models import deposit as DepositCategory


class Category(models.Model):
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories'
    )
    store_type = models.ForeignKey(StoreType, on_delete=models.CASCADE, null=True, blank=True)
    category_name = models.CharField(max_length=50)
    category_code = models.CharField(max_length=50, unique=True)  # e.g. 'GROC', 'BEV'
    vendor_subcategory_reference_id  = models.IntegerField(null=True, blank=True) # This field only for subcategory use to track the vendor's subcategory we will store his id here (This is a indirect connection withn venodr) 
    slug = models.SlugField(max_length=100)
    category_image = models.ImageField(upload_to='store/categories/uploads', null=True, blank=True)
    description = models.TextField(max_length=250, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        # Ensure combination of vendor and slug is unique
        constraints = [
            models.UniqueConstraint(fields=['category_code'], name='unique_category_code')
        ]

    def clean(self):
        self.category_name = self.category_name.capitalize()
        

    def __str__(self):
        return self.category_name
    
    def get_subcategory_count(self):
        return self.subcategories.count()
    
UNIT_TYPE_CHOICES = (
    ('pcs', 'Pieces'),
    ('kg', 'Kilograms'),
    ('g', 'Grams'),
    ('l', 'Liters'),
    ('ml', 'Milliliters'),
    ('m', 'Meters'),
    ('m2', 'Meter Square'),
)

class Product(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='products')
    product_name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=300, blank=True)
    product_desc = models.TextField(blank=True, null=True)
    full_specification = models.TextField(blank=True, default='')
    hsn_number = models.CharField(max_length=8, blank=True, null=True)
    model_number = models.CharField(max_length=20, blank=True, null=True)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=False)
    regular_price = models.DecimalField(max_digits=12, decimal_places=2)
    sales_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    image = models.ImageField(upload_to='store/products/uploads')
    is_available = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    subcategory = models.ForeignKey(Category, related_name='subcategory_products', on_delete=models.CASCADE, blank=True, null=True)
    is_popular = models.BooleanField(default=False, blank=True)
    is_top_collection = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Fields from inventory.product model
    barcode = models.CharField(max_length=25, blank=True, null=True)
    # qty = models.IntegerField(default=0, null=False)
    qty = models.DecimalField(max_digits=10, decimal_places=3, default=0, null=False, help_text="Quantity in selected unit type")
    tax_category     = models.ForeignKey(TaxCategory, on_delete=models.RESTRICT, null=False,blank=False, related_name='products')
    deposit_category = models.ForeignKey(DepositCategory, on_delete=models.RESTRICT, null=True,blank=True, related_name='products')
    
    unit_type = models.CharField(max_length=15, choices=UNIT_TYPE_CHOICES, default='pcs', help_text="Unit type for the product")

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
         constraints = [
            # Enforce barcode uniqueness for non-'N/A' values
            models.UniqueConstraint(
                fields=['vendor', 'barcode'], name='unique_vendor_barcode'),
            # Enforce slug uniqueness
            models.UniqueConstraint(fields=['vendor', 'slug'], name='unique_vendor_slug'),
        ]
    def __str__(self):
        return self.product_name

    def save(self, *args, **kwargs):
        # Automatically set the deposit_category to "Clickmall" if not set
        if not self.deposit_category:
            self.deposit_category = DepositCategory.objects.filter(deposit_category="Clickmall").first()
        
        # Automatically set sales_price to regular_price if not set
        if not self.sales_price:
            self.sales_price = self.regular_price
        super().save(*args, **kwargs)
            
        if not self.barcode:
            self.barcode = self.id

        # Automatically generate slug if not set
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
            ("Stock", f"{self.qty} {self.unit_type}"),
            ("Department Category", self.category.category_name),
            ("Tax Category", self.tax_category.tax_category),
            # ("Deposit Category", self.deposit_category.deposit_category),
        ]

    def get_fields_2(self):
        return [
            ("Barcode", self.barcode),
            ("Name", self.product_name),
            ("Inventory Qty", f"{self.qty} {self.unit_type}"),
            ("Sales Price", self.sales_price),
            ("Cost Price", self.cost_price),
            ("Department Category", self.category.category_name),
            ("Tax Category", self.tax_category.tax_category),
            ("Tax Percentage", self.tax_category.tax_percentage),
            # ("Deposit Category", self.deposit_category.deposit_category),
            # ("Deposit Value", self.deposit_category.deposit_value),
        ]
    
    def get_discount_percentage(self):
        try:
            if self.sales_price and self.regular_price and self.sales_price < self.regular_price:
                discount = (self.regular_price - self.sales_price) / self.regular_price * 100
                discount = float(discount)  # Make sure it's a float
                if discount == int(discount):
                    return int(discount)
                return round(discount, 1)
            return 0
        except (TypeError, ZeroDivisionError):
            return 0
    

class ProductGallery(models.Model):
    product = models.ForeignKey(Product, blank=True, null=True, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='store/products', max_length=355, blank=True, null=True)

    def __str__(self):
        return self.product.product_name

    class Meta:
        verbose_name = 'productgallery'
        verbose_name_plural = 'product gallery'


class MediaUpload(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, blank=True, null=True)
    image = models.ImageField(upload_to='uploaded_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.image.name


class CategoryBrowsePage(models.Model):
    category = models.OneToOneField(Category, on_delete=models.CASCADE)
    banner = models.ImageField(upload_to='browse-banners/', blank=True, null=True)

    def __str__(self):
        return f"{self.category.category_name} Browse Page"


class CategoryBrowseSection(models.Model):
    PAGE_SECTION_TYPES = [
        ('product_slider', 'Product Slider'),
        ('subcategory_slider', 'Subcategory Slider'),
        ('brand_slider', 'Brand Slider'),
        ('image_slider', 'Image Slider'),
        ('custom_heading', 'Custom Heading Only'),
    ]

    browse_page = models.ForeignKey(CategoryBrowsePage, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=255)
    section_type = models.CharField(max_length=50, choices=PAGE_SECTION_TYPES)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} ({self.get_section_type_display()})"
    

class ProductAssignment(models.Model):
    section = models.ForeignKey(CategoryBrowseSection, on_delete=models.CASCADE, related_name='products')
    product = models.ManyToManyField(Product, null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']


class SubCategoryAssignment(models.Model):
    section = models.ForeignKey(CategoryBrowseSection, on_delete=models.CASCADE, related_name='subcategories')
    subcategory = models.ManyToManyField('unified.Category',null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def clean(self):
            if self.pk:  # Only run this if the instance has been saved (i.e., has a primary key)
                from django.core.exceptions import ValidationError
                for subcat in self.subcategory.all():
                    if subcat.parent is None:
                        raise ValidationError("Only subcategories (i.e., categories with a parent) can be assigned here.")

