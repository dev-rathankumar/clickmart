from django.contrib import admin
from .models import Payment, Order, OrderedFood


class OrderedFoodInline(admin.TabularInline):
    model = OrderedFood
    readonly_fields = ('order', 'payment', 'user', 'quantity', 'price', 'amount','status',)
    extra = 0


class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'name', 'phone', 'email', 'total', 'payment_method',  'order_placed_to', 'is_ordered']
    inlines = [OrderedFoodInline]


admin.site.register(Payment)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderedFood)
