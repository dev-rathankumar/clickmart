from django.contrib import admin
from .models import User, UserProfile, DeliveryAddress
from django.contrib.auth.admin import UserAdmin

# Register your models here.

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'username', 'role', 'is_active')
    ordering = ('-date_joined',)
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

class DeliveryAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'city', 'country', 'is_primary')
    list_filter = ('is_primary', 'country', 'city')
    search_fields = ('user__username', 'full_name', 'city')

admin.site.register(User, CustomUserAdmin)
admin.site.register(DeliveryAddress, DeliveryAddressAdmin)
admin.site.register(UserProfile)