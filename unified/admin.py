from django.contrib import admin

from inventory.models import tax
from vendor.models import Vendor
from .models import Product as UnifieldProduct
from .models import ProductGallery, Category
import admin_thumbnails
from import_export.admin import ImportExportModelAdmin
from import_export.admin import ExportMixin
from import_export import resources


class UnifieldProductResource(resources.ModelResource):
    class Meta:
        model = UnifieldProduct
        fields = ("barcode", "vendor", "product_name", "regular_price", "sales_price", 
                  "qty", "cost_price", "category", "category__category_name", 
                  "tax_category", "tax_category__tax_category", "tax_category__tax_percentage",
                  "product_desc")
        export_order = fields
        import_id_fields = ('barcode',)

    # Override dehydrate methods to show human-readable values
    def dehydrate_vendor(self, product):
        return product.vendor.vendor_name # Display vendor's name instead of ID

    def dehydrate_category(self, product):
        return product.category.category_name  # Display category name instead of ID

    def dehydrate_subcategory(self, product):
        return product.subcategory.category_name if product.subcategory else None  # Handle subcategory

    def dehydrate_tax_category(self, product):
        return product.tax_category.tax_category  # Display tax category name instead of ID

    def dehydrate_deposit_category(self, product):
        return product.deposit_category.deposit_category if product.deposit_category else None  # Handle deposit category
    
    def before_import_row(self, row, **kwargs):
        # Get Vendor by name instead of ID
        if 'vendor' in row and row['vendor']:
            vendor_name = row['vendor']
            vendor, _ = Vendor.objects.get_or_create(vendor_name=vendor_name)
            row['vendor'] = vendor.id  # Set the ForeignKey field to the actual Vendor object

        # Get Category by name instead of ID
        if 'category' in row:
            category_name = row['category']
            category = Category.objects.get(category_name=category_name)
            row['category'] = category  # Set the ForeignKey field to the actual Category object

        # Get Subcategory by name instead of ID (if exists)
        if 'subcategory' in row and row['subcategory']:
            subcategory_name = row['subcategory']
            subcategory = Category.objects.get(category_name=subcategory_name)
            row['subcategory'] = subcategory  # Set the ForeignKey field to the actual Subcategory object

        # Get TaxCategory by name instead of ID
        if 'tax_category' in row:
            tax_category_name = row['tax_category']
            tax_category = tax.objects.filter(tax_category=tax_category_name).first()
            row['tax_category'] = tax_category  # Set the ForeignKey field to the actual TaxCategory object

        # Get DepositCategory by name instead of ID (if exists)
        # if 'deposit_category' in row and row['deposit_category']:
        #     deposit_category_name = row['deposit_category']
        #     deposit_category = DepositCategory.objects.get(deposit_category=deposit_category_name)
        #     row['deposit_category'] = deposit_category  # Set the ForeignKey field to the actual DepositCategory object

        return row
    

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('category_name',)}
    list_display = ('category_name', 'vendor', 'updated_at')
    search_fields = ('category_name', 'vendor__vendor_name')


class UnifieldProductAdmin(ImportExportModelAdmin):
    list_display = ['vendor', 'product_name', 'sales_price', 'qty']
    resource_class = UnifieldProductResource


@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name','is_active', 'vendor', 'is_available', 'qty')
    inlines = [ProductGalleryInline]


admin.site.register(Category, CategoryAdmin)
admin.site.register(UnifieldProduct, UnifieldProductAdmin)
admin.site.register(ProductGallery)
