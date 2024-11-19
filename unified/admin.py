from django.contrib import admin
from .models import Product as UnifieldProduct


class ProductAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'product_name', 'sales_price', 'qty']


admin.site.register(UnifieldProduct, ProductAdmin)