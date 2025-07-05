# services/product_collections.py

from unified.models import Product

def get_products_for_collection(logic_type):
    if logic_type == 'popular':
        return Product.objects.filter(is_active=True, is_popular=True,qty__gt=0)[:12]
    elif logic_type == 'low_price':
        return Product.objects.filter(is_active=True,qty__gt=0).order_by('sales_price')[:12]
    # elif logic_type == 'top_rated':
    #     return Product.objects.filter(is_active=True).order_by('-average_rating')[:12]
    elif logic_type == 'latest':
        return Product.objects.filter(is_active=True,qty__gt=0).order_by('-created_date')[:12]
    elif logic_type == 'top_collection':
        return Product.objects.filter(is_active=True, is_top_collection=True,qty__gt=0).order_by('-created_date')[:12]
    else:
        return Product.objects.none()
