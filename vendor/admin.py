from django.contrib import admin
from vendor.models import Vendor, OpeningHour, StoreType, AdBanner


class StoreTypeAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


class VendorAdmin(admin.ModelAdmin):
    list_display = ('user', 'vendor_name', 'store_type', 'is_approved', 'created_at')
    list_display_links = ('user', 'vendor_name')
    list_editable = ('is_approved',)


class OpeningHourAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'day', 'from_hour', 'to_hour')

admin.site.register(Vendor, VendorAdmin)
admin.site.register(OpeningHour, OpeningHourAdmin)
admin.site.register(StoreType, StoreTypeAdmin)
admin.site.register(AdBanner)