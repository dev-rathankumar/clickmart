from .models import Cart
from unified.models import Product, Category, ProductVariantGroup
from inventory.models import tax
from vendor.models import StoreType
from mobile.utils import get_current_event


def get_cart_counter(request, session_cart=None):

    cart_count = 0

    # If a cart dict is passed explicitly (for AJAX/utility use)
    if session_cart is not None:
        cart_count = sum(int(qty) for qty in session_cart.values())
    # Authenticated user
    elif request.user.is_authenticated:
        from django.db.models import Sum
        cart_items = Cart.objects.filter(user=request.user)
        cart_count = cart_items.aggregate(total=Sum('quantity'))['total'] or 0
    # Guest user/session cart
    else:
        cart = request.session.get('cart', {})
        cart_count = sum(int(qty) for qty in cart.values())

    return dict(cart_count=cart_count)

def get_cart_amounts(request, session_cart=None):
    """
    Returns a dictionary with subtotal, tax, grand_total, and tax_dict for the cart.
    Supports both authenticated users (DB) and guests (session cart).
    Handles both regular products and variant products.
    """
    from django.db import models

    subtotal = 0
    tax_value = 0
    tax_dict = []
    grand_total = 0

    # Use passed session_cart, or fallback
    cart = session_cart if session_cart is not None else (request.session.get('cart', {}) if not request.user.is_authenticated else None)

    if request.user.is_authenticated and session_cart is None:
        # Authenticated user - get from database
        cart_items = Cart.objects.filter(user=request.user)
        for item in cart_items:
            product_total = 0
            product = item.product
            
            # Get price from variant if exists, otherwise from product
            if item.product_variant_group and item.product_variant_group.price:
                price = item.product_variant_group.price
            else:
                price = product.sales_price if product.sales_price is not None else product.regular_price
            
            product_total = price * item.quantity
            subtotal += product_total

            # Tax calculation
            if product.tax_category:
                tax_instance = product.tax_category
                tax_amount = round((tax_instance.tax_percentage * product_total) / 100, 2)
                tax_value += tax_amount

                tax_entry = {
                    'tax_category': tax_instance.tax_category,
                    'tax_info': {str(tax_instance.tax_percentage): tax_amount},
                    'product_id': product.id
                }
                tax_dict.append(tax_entry)

    elif cart:  # Guest session cart
        # cart is { 'product_id': quantity } or { 'product_id-variant_id': quantity }
        for cart_key, qty in cart.items():
            try:
                # Check if this is a variant product (has hyphen in key)
                if '-' in cart_key:
                    product_id, variant_id = cart_key.split('-')
                    try:
                        variant = ProductVariantGroup.objects.get(id=variant_id)
                        product = variant.product
                        if variant.price is not None:
                            price = variant.price
                        else:
                            price = product.sales_price if product.sales_price is not None else product.regular_price
                    except ProductVariantGroup.DoesNotExist:
                        continue
                else:
                    # Regular product
                    product_id = cart_key
                    product = Product.objects.get(pk=product_id)
                    price = product.sales_price if product.sales_price is not None else product.regular_price

                product_total = price * int(qty)
                subtotal += product_total

                # Tax calculation
                if product.tax_category:
                    tax_instance = product.tax_category
                    tax_amount = round((tax_instance.tax_percentage * product_total) / 100, 2)
                    tax_value += tax_amount

                    tax_entry = {
                        'tax_category': tax_instance.tax_category,
                        'tax_info': {str(tax_instance.tax_percentage): tax_amount},
                        'product_id': product.id
                    }
                    tax_dict.append(tax_entry)
            except (Product.DoesNotExist, ValueError):
                continue

    grand_total = subtotal

    return {
        'subtotal': subtotal,
        'tax': tax_value,
        'grand_total': grand_total,
        'tax_dict': tax_dict,
    }

def categories_processor(request):
    categories = Category.objects.filter(parent__isnull=True, is_active=True).prefetch_related('subcategories').distinct()[:5]
    return {'categories': categories}

def store_type_processor(request):
    store_types = StoreType.objects.all()
    return{'store_types':store_types}


def categories_home_processor(request):
    categories_home = Category.objects.filter(parent=None, is_active=True)
    return {'categories_home': categories_home}

def get_event_for_today(request):
    current_event = get_current_event()
    return {'current_event': current_event}