from django.contrib import admin
from .models import HomePageBanner, CategoryBanner, ProductCollection
from django.utils.html import format_html
from adminsortable2.admin import SortableAdminMixin


class HomePageBannerAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['thumbnail', 'vendor', 'link', 'is_active', 'order']
    list_editable = ['is_active']
    readonly_fields = ['thumbnail']

    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" style="border-radius: 8px;" />', obj.image.url)
        return "No Image"
    thumbnail.short_description = 'Preview'


class CategoryBannerAdmin(admin.ModelAdmin):
    list_display = ['thumbnail', 'category', 'link', 'is_active']
    list_editable = ['is_active']
    list_filter = ['category']
    readonly_fields = ['thumbnail']

    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" style="border-radius: 8px;" />', obj.image.url)
        return "No Image"
    thumbnail.short_description = 'Preview'


class ProductCollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'logic', 'active')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('active',)


admin.site.register(HomePageBanner, HomePageBannerAdmin)
admin.site.register(CategoryBanner, CategoryBannerAdmin)
admin.site.register(ProductCollection, ProductCollectionAdmin)