from .models import Cart
from menu.models import Product,Category
from inventory.models import tax
from vendor.models import StoreType
def get_cart_counter(request):
    cart_count = 0
    if request.user.is_authenticated:
        try:
            cart_items = Cart.objects.filter(user=request.user)
            if cart_items:
                for cart_item in cart_items:
                    cart_count += cart_item.quantity
            else:
                cart_count = 0
        except:
            cart_count = 0
    return dict(cart_count=cart_count)


def get_cart_amounts(request):
    subtotal = 0
    tax_value = 0
    grand_total = 0
    tax_dict = []
    
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)
        
        for item in cart_items:
            product_total = 0
            product = Product.objects.get(pk=item.product.id)

            # Calculate product total based on sales or regular price
            if product.sales_price is not None:
                product_total += (product.sales_price * item.quantity)
                subtotal += (product.sales_price * item.quantity)
            else:
                product_total += (product.regular_price * item.quantity)
                subtotal += (product.regular_price * item.quantity)

            # Fetch tax information
            tax_instance = tax.objects.get(id=product.tax_category.id)
            tax_amount = round((tax_instance.tax_percentage * product_total) / 100, 2)
            tax_value += tax_amount

            # Add tax entry with product ID
            tax_category = tax_instance.tax_category
            tax_percentage = tax_instance.tax_percentage

            # Create tax entry with product ID
            tax_entry = {
                'tax_category': tax_category,
                'tax_info': {
                    str(tax_percentage): tax_amount
                },
                'product_id': product.id  # Only product ID is included
            }
            
            # Append to tax_dict without breaking the current structure
            tax_dict.append(tax_entry)

        grand_total = subtotal
        print(tax_dict)

    return dict(subtotal=subtotal, tax=tax_value, grand_total=grand_total, tax_dict=tax_dict)

def categories_processor(request):
    categories = Category.objects.filter(parent__isnull=True, is_active=True).prefetch_related('subcategories').distinct()[:5]
    return {'categories': categories}

def store_type_processor(request):
    store_types = StoreType.objects.all()
    return{'store_types':store_types}


def categories_home_processor(request):
    categories_home = Category.objects.filter(parent=None, is_active=True)
    return {'categories_home': categories_home}