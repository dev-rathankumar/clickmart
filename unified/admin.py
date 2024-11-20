from django.contrib import admin
from .models import Product as UnifieldProduct
from .models import ProductGallery, Category
import admin_thumbnails


class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('category_name',)}
    list_display = ('category_name', 'vendor', 'updated_at')
    search_fields = ('category_name', 'vendor__vendor_name')


class ProductAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'product_name', 'sales_price', 'qty']


@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name','is_active', 'vendor', 'is_available', 'qty')
    inlines = [ProductGalleryInline]


admin.site.register(Category, CategoryAdmin)
admin.site.register(UnifieldProduct, ProductAdmin)
admin.site.register(ProductGallery)
