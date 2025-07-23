from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import UserProfile, DeliveryAddress
from .context_processors import get_cart_counter, get_cart_amounts
from unified.models import Category, CategoryBrowsePage, ProductGallery,VariantAttributeValue, ProductVariantGroup

from unified.models import Product

from vendor.models import OpeningHour, Vendor
from django.db.models import Prefetch
from .models import Cart
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D # ``D`` is a shortcut for ``Distance``
from django.contrib.gis.db.models.functions import Distance

from datetime import date, datetime
from orders.forms import OrderForm
from django.conf import settings
import json
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages

from marketplace.models import Cart
from django.db.models import Sum

from django.db import models

from django.db.models import Count, OuterRef, Subquery
from django.core.paginator import Paginator
from foodOnline_main.views import get_or_set_current_location
from django.db.models import Sum, F, Value
from django.db.models.functions import Coalesce
from collections import defaultdict
from django.forms.models import model_to_dict
from .utils import get_matching_variant_group,get_variant_combinations
from django.core.serializers.json import DjangoJSONEncoder

def marketplace(request):
    if get_or_set_current_location(request) is not None:

            pnt = GEOSGeometry('POINT(%s %s)' % (get_or_set_current_location(request)))

            vendors = Vendor.objects.filter(user_profile__location__distance_lte=(pnt, D(km=10000))).annotate(distance=Distance("user_profile__location", pnt)).order_by("distance")

            for v in vendors:
                v.kms = round(v.distance.km, 1)
    else:
        vendors = Vendor.objects.filter(is_approved=True, user__is_active=True)

    vendor_count = vendors.count()
    search_query = request.GET.get('search', None)
    
    if search_query:
        vendors = vendors.filter(
            Q(vendor_name__icontains=search_query) |
            Q(vendor_slug__icontains=search_query) |
            Q(store_type__name__icontains=search_query)
        )

    vendors = list(vendors)  # evaluate queryset
    vendors.sort(key=lambda v: v.is_open() or False, reverse=True)  # Open vendors first
    paginator = Paginator(vendors, 10)
    page_number = request.GET.get('page')
    page_vendors = paginator.get_page(page_number)

    context = {
        'vendors': page_vendors,
        'vendor_count': vendor_count,
    }
    return render(request, 'marketplace/listings.html', context)

def vendor_detail(request, vendor_slug, category_id=None, subcategory_id=None):
    vendor = get_object_or_404(Vendor, vendor_slug=vendor_slug)
    category_products = Product.objects.filter(vendor=vendor, is_available=True, is_active=True)
    used_category_ids = category_products.values_list('category_id', flat=True).distinct()
    categories = Category.objects.filter(id__in=used_category_ids,is_active=True, parent=None, store_type=vendor.store_type).prefetch_related(Prefetch('subcategories',  queryset=Category.objects.filter(vendor_subcategory_reference_id=vendor.id, is_active=True) ))

    # Handle search query
    search_query = request.GET.get('search', None)
    sort_type = request.GET.get('sort', None)

    # Annotate product count for each category
    for cat in categories:
        subcat_ids = cat.subcategories.filter(is_active=True,vendor_subcategory_reference_id=vendor.id).values_list('id', flat=True)
        cat.product_count = Product.objects.filter(
            subcategory__in=subcat_ids,
            is_available=True,
            vendor=vendor,
            is_active=True
        ).count()

    if subcategory_id:
        # Filter by subcategory
        selected_subcategory = get_object_or_404(Category, id=subcategory_id, is_active=True)
        products = Product.objects.filter(
            subcategory=selected_subcategory, 
            is_available=True, 
            is_active=True, 
            vendor=vendor
        )
    elif category_id:
        # Filter by category
        selected_category = get_object_or_404(Category, id=category_id, is_active=True, store_type=vendor.store_type)
        products = Product.objects.filter(
            category=selected_category,
            is_available=True,
            is_active=True,
            vendor=vendor
        )
    else:
        # Show all products
        products = Product.objects.filter(is_available=True, is_active=True, vendor=vendor)
    
    # Apply search filter
    if search_query:
        products = products.filter(
            models.Q(product_name__icontains=search_query) | models.Q(product_desc__icontains=search_query)
        )
        
    if sort_type == 'dsec':
        products =  products.order_by('-sales_price')
    if sort_type == "asec":
        products =  products.order_by('sales_price')




    opening_hours = OpeningHour.objects.filter(vendor=vendor).order_by('day', 'from_hour')
    today_date = date.today()
    today = today_date.isoweekday()
    current_opening_hours = OpeningHour.objects.filter(vendor=vendor, day=today)
    
    cart_items = Cart.objects.filter(user=request.user) if request.user.is_authenticated else None

    user_cart = Cart.objects.filter(user=request.user) if request.user.is_authenticated else []
    cart_vendors = set(item.product.vendor_id for item in user_cart)

    for product in products:
        # True if cart is not empty and this product's vendor is NOT in the cart's vendors
        product.is_different_vendor_for_cart = bool(cart_vendors) and (product.vendor_id not in cart_vendors)


      # Implement pagination
    paginator = Paginator(products, 20)  # Show 20 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    show_pagination = paginator.num_pages > 1


    
    # Vendor distance 
    if get_or_set_current_location(request) is not None:

        pnt = GEOSGeometry('POINT(%s %s)' % (get_or_set_current_location(request)))

        vendors = Vendor.objects.filter(user_profile__location__distance_lte=(pnt, D(km=100000))).annotate(distance=Distance("user_profile__location", pnt)).order_by("distance")
        print("vendros ===> ", vendors)
        for v in vendors:
            if v.id == vendor.id: 
                vendor.kms = round(v.distance.km, 1)

      

    if request.user.is_authenticated:
        cart_items = []
        for cart_obj in Cart.objects.filter(user=request.user).order_by('created_at'):
            cart_items.append({
                'product': cart_obj.product,
                'quantity': cart_obj.quantity,
                'cart_id': cart_obj.id,  # DB cart uses Cart PK
            })
    else:
        cart = request.session.get('cart', {})
        cart_items = []
        
        # Separate regular products and variant products
        regular_products = {}
        variant_products = {}
        
        for cart_id, quantity in cart.items():
            if '-' in cart_id:
                # Variant product (format: "product_id-variant_id")
                product_id, variant_id = cart_id.split('-')
                variant_products.setdefault(product_id, {})[variant_id] = quantity
            else:
                # Regular product (format: "product_id")
                regular_products[cart_id] = quantity
        
        # Convert string IDs to integers for database lookup
        product_id_ints = [int(pid) for pid in regular_products.keys()]
        product_id_ints.extend([int(pid) for pid in variant_products.keys()])
        
        # Fetch all products and variants in bulk
        products = Product.objects.filter(id__in=product_id_ints).in_bulk()
        
        variant_ids = [int(vid) for vid_dict in variant_products.values() for vid in vid_dict.keys()]
        variants = ProductVariantGroup.objects.filter(id__in=variant_ids).in_bulk()
        
        # Build cart items for regular products
        for product_id_str, quantity in regular_products.items():
            product_id = int(product_id_str)
            product = products.get(product_id)
            if product:
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'variant': None,
                    'cart_id': product_id_str,  # Keep original string ID for session
                    'price': product.sales_price or product.regular_price,
                })
        
        # Build cart items for variant products
        for product_id_str, variant_dict in variant_products.items():
            product_id = int(product_id_str)
            product = products.get(product_id)
            if product:
                for variant_id_str, quantity in variant_dict.items():
                    variant_id = int(variant_id_str)
                    variant = variants.get(variant_id)
                    if variant:
                        cart_id = f"{product_id_str}-{variant_id_str}"
                        cart_items.append({
                            'product': product,
                            'quantity': quantity,
                            'variant': variant,
                            'cart_id': cart_id,
                            'price': variant.price,
                        })

    # Get product IDs - handle both dictionary items and model instances
    cart_product_ids = set()
    for item in cart_items:
        if isinstance(item, dict) and 'product' in item and item['product']:
            cart_product_ids.add(item['product'].id)
        elif hasattr(item, 'product') and item.product:  # For model instances
            cart_product_ids.add(item.product.id)
    context = {
        'vendor': vendor,
        'categories': categories,
        'cart_items': cart_items,
        'opening_hours': opening_hours,
        'current_opening_hours': current_opening_hours,
        'products': page_obj,
        'search_query': search_query, 
        'show_pagination':show_pagination,
        'cart_product_ids': cart_product_ids,
        'cart_items': cart_items,
        'total_vendor_products': products,

    }
    return render(request, 'marketplace/vendor_detail.html', context)

def view_Product(request, vendor_slug, product_slug):
    # Get the main product and vendor
    product = get_object_or_404(Product, vendor__vendor_slug=vendor_slug, slug=product_slug)
    vendor = get_object_or_404(Vendor, vendor_slug=vendor_slug)
    
    # Get user's primary address if authenticated
    address = DeliveryAddress.objects.filter(user=request.user, is_primary=True).first() if request.user.is_authenticated else None
    
    # Calculate vendor distance if location is available
    if get_or_set_current_location(request) is not None:
        pnt = GEOSGeometry('POINT(%s %s)' % (get_or_set_current_location(request)))
        vendors = Vendor.objects.filter(
            user_profile__location__distance_lte=(pnt, D(km=100000))
        ).annotate(distance=Distance("user_profile__location", pnt)).order_by("distance")
        
        for v in vendors:
            if v.id == vendor.id: 
                vendor.kms = round(v.distance.km, 1)

    # Initialize cart-related variables
    chkCart = None
    chkCart_count = 0
    cart_items = []
    cart_product_ids = set()

    if request.user.is_authenticated:
        # Authenticated user - get cart from database
        chkCart = Cart.objects.filter(product=product, user=request.user)
        chkCart_count = chkCart.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
        
        cart_items = [
            {
                'product': cart_obj.product,
                'quantity': cart_obj.quantity,
                'variant': cart_obj.product_variant_group,
                'cart_id': cart_obj.id,
                'price': cart_obj.product_variant_group.price if cart_obj.product_variant_group else cart_obj.product.sales_price,
            }
            for cart_obj in Cart.objects.filter(user=request.user).order_by('created_at')
        ]
    else:
        # Guest user - get cart from session
        cart = request.session.get('cart', {})
        chkCart_count = 0
        
        # Check both regular product and any variants in cart
        product_id_str = str(product.id)
        for cart_id, quantity in cart.items():
            if cart_id.startswith(product_id_str):
                if '-' in cart_id:
                    # This is a variant of our product
                    variant_id = cart_id.split('-')[1]
                    try:
                        variant = ProductVariantGroup.objects.get(id=variant_id, product=product)
                        chkCart_count += quantity
                    except ProductVariantGroup.DoesNotExist:
                        continue
                else:
                    # This is the base product
                    chkCart_count += quantity
        
        # Build full cart items list for guest user
        regular_products = {}
        variant_products = {}
        
        for cart_id, quantity in cart.items():
            if '-' in cart_id:
                product_id, variant_id = cart_id.split('-')
                variant_products.setdefault(product_id, {})[variant_id] = quantity
            else:
                regular_products[cart_id] = quantity
        
        # Fetch all products and variants in bulk
        product_ids = list(regular_products.keys()) + list(variant_products.keys())
        products_in_cart = Product.objects.filter(id__in=product_ids).in_bulk()
        
        variant_ids = []
        for variant_dict in variant_products.values():
            variant_ids.extend(variant_dict.keys())
        variants = ProductVariantGroup.objects.filter(id__in=variant_ids).in_bulk()
        
        # Build cart items
        for product_id, quantity in regular_products.items():
            cart_product = products_in_cart.get(product_id)
            if cart_product:
                cart_items.append({
                    'id': cart_product.id,
                    'product': cart_product,
                    'quantity': quantity,
                    'variant': None,
                    'cart_id': product_id,
                    'price': cart_product.sales_price or cart_product.regular_price,
                })
                cart_product_ids.add(cart_product.id)
        
        for product_id, variant_dict in variant_products.items():
            cart_product = products_in_cart.get(product_id)
            if cart_product:
                for variant_id, quantity in variant_dict.items():
                    variant = variants.get(variant_id)
                    if variant:
                        cart_items.append({
                            'id': f"{product_id}-{variant_id}",
                            'product': cart_product,
                            'quantity': quantity,
                            'variant': variant,
                            'cart_id': f"{product_id}-{variant_id}",
                            'price': variant.price,
                        })
                        cart_product_ids.add(cart_product.id)

    # Get product gallery and similar products
    product_gallery = ProductGallery.objects.filter(product=product)
    similar_products = Product.objects.filter(
        category=product.category,
        is_available=True,
    ).exclude(id=product.id).annotate(
        total_sold=Coalesce(Sum('orderedfood__quantity'), 0)
    ).order_by('-total_sold')[:10]

    # Prepare variant data
    product_variant_values = VariantAttributeValue.objects.filter(
        product=product
    ).select_related('attribute')
    
    attribute_groups = defaultdict(list)
    for value in product_variant_values:
        attribute_groups[value.attribute].append(value)
    
    product_variant_map = [
        {
            "attribute": attr,
            "values": sorted(vals, key=lambda v: v.value)
        }
        for attr, vals in sorted(attribute_groups.items(), key=lambda t: t[0].name)
    ]
    product_variant_map_json = json.dumps([
        {
            "attribute": {"name": attr_group["attribute"].name},
            "values": [{"id": str(v.id), "value": v.value} for v in attr_group["values"]]
        }
        for attr_group in product_variant_map
    ], cls=DjangoJSONEncoder)

    variant_combinations = get_variant_combinations(product)

    context = {
        'vendor': vendor,
        'product': product,
        'similar_products': similar_products,
        'check_cart': chkCart,
        'chkCart_count': chkCart_count,
        'product_gallery': product_gallery,
        'address': address,
        'cart_items': cart_items,
        'cart_product_ids': cart_product_ids,
        'product_variant_map': product_variant_map,
        'product_variant_map_json': product_variant_map_json, 
        'variant_combinations_json': json.dumps(variant_combinations)
    }
    
    return render(request, 'vendor/product_view.html', context)

def get_cart_count(request):
    if request.method == "POST":
        data = json.loads(request.body)
        product_id = data.get('product_id')
        print("Product ID:", product_id)
        selected_value_ids = data.get('attributes', [])
        
        try:
            product = Product.objects.get(id=product_id)
            variant = None
            
            # Find the ProductVariantGroup with exact attribute values if attributes are selected
            if selected_value_ids:
                qset = ProductVariantGroup.objects.filter(product=product)
                for value_id in selected_value_ids:
                    qset = qset.filter(attribute__id=value_id)
                variant = qset.distinct().first()
            print("Variant:", variant)
            print("Variant ID:", variant.id)
            if request.user.is_authenticated:
                # Handle logged-in users (existing logic)
                cart_items = Cart.objects.filter(user=request.user, product=product)
                if variant:
                    cart_items = cart_items.filter(product_variant_group=variant)
                
                total_quantity = sum(item.quantity for item in cart_items)
                return JsonResponse({
                    'success': True,
                    'quantity': total_quantity,
                    'has_items': cart_items.exists()
                })
            else:
                # Handle anonymous users with session cart
                cart = request.session.get('cart', {})
                total_quantity = 0
                
                # Find the matching variant group based on selected attributes
                variant_group = None
                if selected_value_ids:
                    qset = ProductVariantGroup.objects.filter(product=product)
                    for value_id in selected_value_ids:
                        qset = qset.filter(attribute__id=value_id)
                    variant_group = qset.distinct().first()
                
                # Build the cart key to look for
                if variant_group:
                    cart_key = f"{product_id}-{variant_group.id}"
                    total_quantity = cart.get(cart_key, 0)
                else:
                    # For base product (no variants)
                    cart_key = str(product_id)
                    total_quantity = cart.get(cart_key, 0)
                
                return JsonResponse({
                    'success': True,
                    'quantity': total_quantity,
                    'has_items': total_quantity > 0
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
def find_variations_data(request):
    """
    Expects POST with:
    - product_id
    - attributes: list of attribute value ids (e.g., [1, 5])
    Returns: image, price, stock, etc. of the matching ProductVariantGroup
    """
    if request.method == "POST":
        data = json.loads(request.body)
        product_id = data.get('product_id')
        selected_value_ids = data.get('attributes', [])  # list of value ids

        try:
            product = Product.objects.get(id=product_id)
            # Find the ProductVariantGroup with exact attribute values
            qset = ProductVariantGroup.objects.filter(product=product)
            for value_id in selected_value_ids:
                qset = qset.filter(attribute__id=value_id)
            variant = qset.distinct().first()
            if variant:
                result = {
                    "success": True,
                    "image": variant.image.url if variant.image else "",
                    "price": str(variant.price),
                    "stock": str(variant.stock),
                }
            else:
                result = {"success": False,'Notfounded':True, "error": "No such variant found."}
        except Product.DoesNotExist:
            result = {"success": False, "error": "Product not found."}
        return JsonResponse(result)
    return JsonResponse({"success": False, "error": "Invalid request."})



def add_to_cart(request, food_id):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            product = Product.objects.get(id=food_id)
        except Product.DoesNotExist:
            return JsonResponse({'status': 'Failed', 'message': 'This product does not exist!'})
        
        try:
            qty = int(request.GET.get('quantity', 1))
            if qty < 1:
                qty = 1
        except (ValueError, TypeError):
            qty = 1
            
        # Get variant data
        variant_data = {}
        for key in request.GET:
            if key.startswith('variants[') and key.endswith(']'):
                attr = key[9:-1]
                variant_data[attr] = request.GET.get(key)

        # Get matching variant group if variants exist
        variant_group = None
        if variant_data:
            variant_group = get_matching_variant_group(product, variant_data)

        # --- Authenticated user ---
        if request.user.is_authenticated:
            try:
                chkCart = Cart.objects.get(user=request.user, product=product, product_variant_group=variant_group)
                new_quantity = chkCart.quantity + qty
                if new_quantity > (variant_group.stock if variant_group else product.qty):
                    cart_counter = get_cart_counter(request)
                    return JsonResponse({
                        'status': 'Failed',
                        'cart_counter': cart_counter['cart_count'],
                        'qty': chkCart.quantity,
                        'cart_amount': get_cart_amounts(request)
                    })
                chkCart.quantity = new_quantity
                chkCart.save()
                cart_counter = get_cart_counter(request)
                return JsonResponse({
                    'status': 'Success',
                    'message': 'Increased the cart quantity',
                    'cart_counter': cart_counter['cart_count'],
                    'qty': chkCart.quantity,
                    'cart_amount': get_cart_amounts(request),
                    'variant_group': bool(variant_group),
                })
            except Cart.DoesNotExist:
                available_qty = variant_group.stock if variant_group else product.qty
                if available_qty < qty:
                    cart_counter = get_cart_counter(request)
                    return JsonResponse({
                        'status': 'Failed',
                        'message': f'{product.product_name} is out of stock.',
                        'cart_counter': cart_counter['cart_count'],
                        'qty': 0,
                        'cart_amount': get_cart_amounts(request),
                        'variant_group': bool(variant_group),
                    })
                chkCart = Cart.objects.create(
                    user=request.user, 
                    product=product, 
                    quantity=qty, 
                    product_variant_group=variant_group
                )
                cart_counter = get_cart_counter(request)
                return JsonResponse({
                    'status': 'Success',
                    'message': 'Added the product to the cart',
                    'cart_counter': cart_counter['cart_count'],
                    'qty': chkCart.quantity,
                    'cart_amount': get_cart_amounts(request),
                    'variant_group': bool(variant_group),
                })

        # --- Guest user (session cart) ---
        else:
            cart = request.session.get('cart', {})
            
            # Create a unique key for this product + variant combination
            if variant_group:
                cart_id = f"{product.id}-{variant_group.id}"
            else:
                cart_id = str(product.id)
            
            prev_qty = cart.get(cart_id, 0)
            new_qty = prev_qty + qty
            
            # Check stock
            available_qty = variant_group.stock if variant_group else product.qty
            if new_qty > available_qty:
                return JsonResponse({
                    'status': 'Failed',
                    'cart_counter': sum(int(q) for q in cart.values()),
                    'qty': prev_qty,
                    'cart_amount': get_cart_amounts(request, session_cart=cart),
                })
                
            cart[cart_id] = new_qty
            request.session['cart'] = cart
            request.session.modified = True

            return JsonResponse({
                'status': 'Success',
                'message': 'Added the product to the cart',
                'cart_counter': sum(int(q) for q in cart.values()),
                'qty': cart[cart_id],
                'cart_amount': get_cart_amounts(request, session_cart=cart),
                'variant_group': bool(variant_group),
            })
    else:
        return JsonResponse({'status': 'Failed', 'message': 'Invalid request!'})
    

def decrease_cart(request, food_id):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            product = Product.objects.get(id=food_id)
        except Product.DoesNotExist:
            return JsonResponse({'status': 'Failed', 'message': 'This product does not exist!'})

        # Get variant data
        variant_data = {}
        for key in request.GET:
            if key.startswith('variants[') and key.endswith(']'):
                attr = key[9:-1]
                variant_data[attr] = request.GET.get(key)

        variant_group = get_matching_variant_group(product, variant_data) if variant_data else None

        if request.user.is_authenticated:
            try:
                chkCart = Cart.objects.get(user=request.user, product=product, product_variant_group=variant_group)
                if chkCart.quantity > 1:
                    chkCart.quantity -= 1
                    chkCart.save()
                else:
                    chkCart.delete()
                    chkCart.quantity = 0
                cart_counter = get_cart_counter(request)
                return JsonResponse({
                    'status': 'Success',
                    'cart_counter': cart_counter['cart_count'],
                    'qty': chkCart.quantity,
                    'cart_amount': get_cart_amounts(request),
                    'variant_group': bool(variant_group),
                })
            except Cart.DoesNotExist:
                return JsonResponse({'status': 'Failed', 'message': 'You do not have this item in your cart!'})
        else:
            cart = request.session.get('cart', {})
            
            # Create unique key for product + variant combination
            cart_id = f"{product.id}-{variant_group.id}" if variant_group else str(product.id)
            
            qty = int(cart.get(cart_id, 0))
            if qty > 1:
                cart[cart_id] = qty - 1
                new_qty = cart[cart_id]
            elif qty == 1:
                del cart[cart_id]
                new_qty = 0
            else:
                return JsonResponse({'status': 'Failed', 'message': 'You do not have this item in your cart!'})
            
            request.session['cart'] = cart
            request.session.modified = True
            return JsonResponse({
                'status': 'Success',
                'cart_counter': sum(int(q) for q in cart.values()),
                'qty': new_qty,
                'cart_amount': get_cart_amounts(request, session_cart=cart),
                'variant_group': bool(variant_group),
            })
    else:
        return JsonResponse({'status': 'Failed', 'message': 'Invalid request!'})
def cart(request):
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user).order_by('created_at').select_related(
            'product', 'product_variant_group'
        )
    else:
        cart = request.session.get('cart', {})
        cart_items = []
        # Separate regular products and variant products
        regular_products = {}
        variant_products = {}
        
        for cart_id, quantity in cart.items():
            if '-' in cart_id:
                # Variant product
                product_id, variant_id = cart_id.split('-')
                variant_products.setdefault(product_id, {})[variant_id] = quantity
            else:
                # Regular product
                regular_products[cart_id] = quantity
        
        # Fetch all products and variants in bulk
        product_ids = list(regular_products.keys()) + list(variant_products.keys())
        products = Product.objects.filter(id__in=product_ids).in_bulk()
        
        variant_ids = []
        for variant_dict in variant_products.values():
            variant_ids.extend(variant_dict.keys())
        
        variants = ProductVariantGroup.objects.filter(id__in=variant_ids).in_bulk()
        
        # Build cart items for regular products
        for product_id, quantity in regular_products.items():
            product = products.get(int(product_id))  # Convert to int since IDs are numeric
            if product:
                cart_items.append({
                    'id': product.id,
                    'product': product,
                    'quantity': quantity,
                    'product_variant_group': None,
                    'cart_id': product_id,  # Use consistent key name
                    'price': product.sales_price or product.regular_price,
                })
        
        # Build cart items for variant products
        for product_id, variant_dict in variant_products.items():
            product = products.get(int(product_id))  # Convert to int
            if product:
                for variant_id, quantity in variant_dict.items():
                    variant = variants.get(int(variant_id))  # Convert to int
                    if variant:
                        cart_items.append({
                            'id': f"{product_id}-{variant_id}",
                            'product': product,
                            'quantity': quantity,
                            'product_variant_group': variant,
                            'cart_id': f"{product_id}-{variant_id}",
                            'price': variant.price,
                        })


    context = {
        'cart_items': cart_items,
    }
    return render(request, 'marketplace/cart.html', context)

# def delete_cart(request, cart_id):
#     if request.user.is_authenticated:
#         if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#             try:
#                 # Check if the cart item exists
#                 cart_item = Cart.objects.get(user=request.user, id=cart_id)
#                 if cart_item:
#                     product = Product.objects.get(id=cart_item.product.id)
#                     # product.qty +=cart_item.quantity
#                     # product.save()
#                     cart_item.delete()
#                     return JsonResponse({'status': 'Success', 'message': 'Cart item has been deleted!', 'cart_counter': get_cart_counter(request), 'cart_amount': get_cart_amounts(request)})
#             except:
#                 return JsonResponse({'status': 'Failed', 'message': 'Cart Item does not exist!'})
#         else:
#             return JsonResponse({'status': 'Failed', 'message': 'Invalid request!'})


def delete_cart(request, cart_id):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Authenticated user: remove from DB
        if request.user.is_authenticated:
            try:
                cart_item = Cart.objects.get(user=request.user, id=cart_id)
                cart_item.delete()
                cart_counter = get_cart_counter(request)
                return JsonResponse({
                    'status': 'Success',
                    'message': 'Cart item has been deleted!',
                    'cart_counter': cart_counter['cart_count'],
                    'cart_amount': get_cart_amounts(request)
                })
            except Cart.DoesNotExist:
                return JsonResponse({'status': 'Failed', 'message': 'Cart Item does not exist!'})
        
        # Guest user: remove from session cart
        else:
            cart = request.session.get('cart', {})
            
            # Check if this is a variant product (has hyphen in key)
            if '-' in str(cart_id):
                # For variant products, cart_id should be the full composite key
                cart_id = str(cart_id)
            else:
                # For regular products, cart_id is just the product ID
                cart_id = str(cart_id)
            
            if cart_id in cart:
                del cart[cart_id]
                request.session['cart'] = cart
                request.session.modified = True
                
                return JsonResponse({
                    'status': 'Success',
                    'message': 'Cart item has been deleted!',
                    'cart_counter': sum(int(qty) for qty in cart.values()),
                    'cart_amount': get_cart_amounts(request, session_cart=cart)
                })
            else:
                return JsonResponse({'status': 'Failed', 'message': 'Cart Item does not exist!'})
    else:
        return JsonResponse({'status': 'Failed', 'message': 'Invalid request!'})
    
def search(request):
    if not 'address' in request.GET:
        return redirect('marketplace')
    else:
        address = request.GET['address']
        latitude = request.GET['lat']
        longitude = request.GET['lng']
        radius = request.GET['radius']
        keyword = request.GET['keyword']

        # get vendor ids that has the food item the user is looking for
        fetch_vendors_by_products = Product.objects.filter(product_name__icontains=keyword, is_available=True).values_list('vendor', flat=True)
        
        vendors = Vendor.objects.filter(Q(id__in=fetch_vendors_by_products) | Q(vendor_name__icontains=keyword, is_approved=True, user__is_active=True))
        if latitude and longitude and radius:
            pnt = GEOSGeometry('POINT(%s %s)' % (longitude, latitude))

            vendors = Vendor.objects.filter(Q(id__in=fetch_vendors_by_products) | Q(vendor_name__icontains=keyword, is_approved=True, user__is_active=True),
            user_profile__location__distance_lte=(pnt, D(km=radius))
            ).annotate(distance=Distance("user_profile__location", pnt)).order_by("is_open","distance")

            for v in vendors:
                v.kms = round(v.distance.km, 1)
        vendor_count = vendors.count()
        context = {
            'vendors': vendors,
            'vendor_count': vendor_count,
            'source_location': address,
        }


        return render(request, 'marketplace/listings.html', context)




def checkout(request):
    cart_items = Cart.objects.filter(user=request.user).order_by('created_at')
    cart_count = cart_items.count()
    for item in cart_items:
        product = item.product
        if product.qty == 0:
            messages.error(request, f"Sorry, the product '{product}' is out of stock. Please order another product.")
            item.delete()  # delete the cart item that is out of stock
            return redirect('cart')
        elif item.quantity > product.qty:
            messages.error(request, f"Sorry, only {product.qty} quantity of '{product}' is available. You requested {item.quantity}.")
            return redirect('cart')
    if cart_count <= 0:
        return redirect('marketplace')

    user_profile = UserProfile.objects.get(user=request.user)
    default_values = {
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'phone': request.user.phone_number,
        'email': request.user.email,
        'address': user_profile.address,
        'country': user_profile.country,
        'state': user_profile.state,
        'city': user_profile.city,
        'pin_code': user_profile.pin_code,
    }
    # else:
    #     delivery_address=None
    # if delivery_address:
    #     full_name = delivery_address.full_name.strip()
    #     # Split by space
    #     name_parts = full_name.split()

    #     if len(name_parts) >= 2:
    #         first_name = name_parts[0]
    #         last_name = ' '.join(name_parts[1:])  # supports middle names too
    #     else:
    #         first_name = name_parts[0]
    #         last_name = request.user.last_name  # fallback to user's last name
    #     default_values = {
    #         'first_name': first_name,
    #         'last_name':last_name,
    #         'phone': delivery_address.phone_number,
    #         'email': request.user.email,
    #         'address': f"{delivery_address.street_address} {delivery_address.apartment_address if delivery_address.apartment_address else ''}",
    #         'country': delivery_address.country,
    #         'state': delivery_address.state,
    #         'city': delivery_address.city,
    #         'pin_code': delivery_address.postal_code,
    #     }
    # else:
    #     messages.warning(request, "Please set an address to proceed to the next step.")
    #     return redirect("address_book")
    form = OrderForm(initial=default_values)
    RZP_KEY_ID = settings.RZP_KEY_ID
    RZP_KEY_SECRET = settings.RZP_KEY_SECRET
    if not (RZP_KEY_ID and RZP_KEY_SECRET):
        RZP_LOAD = False
    else:
        RZP_LOAD = True
    context = {
        'form': form,
        'cart_items': cart_items,
        'RZP_LOAD': RZP_LOAD,
    }
    return render(request, 'marketplace/checkout.html', context)



def All_products(request, category_id=None, subcategory_id=None):
    # Get only base categories (top-level)
    categories = Category.objects.filter(is_active=True, parent=None)

    # Annotate product count for each top-level category
    for cat in categories:
        # Get all active subcategory IDs under this category
        subcat_ids = cat.subcategories.filter(is_active=True).values_list('id', flat=True)
        # Include the main category itself in the filter
        all_category_ids = list(subcat_ids) + [cat.id]

        # Count all products that belong to this category or its subcategories
        cat.product_count = Product.objects.filter(
            category__id__in=all_category_ids,
            is_available=True,
            is_active=True
        ).count()

    search_query = request.GET.get('search', None)
    store_type = request.GET.get('store_type', None)
    sort_type = request.GET.get('sort', None)
    search_type = request.GET.get('type', 'products')

    # Initialize context with default values
    context = {
        'categories': categories,
        'search_type': search_type,
        'search_query': search_query,
        'cart_items': [],
        'cart_product_ids': set(),  # Initialize with empty set
    }

    if search_type == 'stores':
        if get_or_set_current_location(request) is not None:
            location = get_or_set_current_location(request)
            if location is not None:
                lng, lat = location
                pnt = GEOSGeometry(f'POINT({lng} {lat})', srid=4326)
                vendors = Vendor.objects.filter(
                    user_profile__location__distance_lte=(pnt, D(km=10000))
                ).annotate(distance=Distance("user_profile__location", pnt)).order_by("distance")
            for v in vendors:
                v.kms = round(v.distance.km, 1)
        else:
            vendors = Vendor.objects.filter(is_approved=True, user__is_active=True)
        
        if search_query:
            vendors = vendors.filter(
                models.Q(vendor_name__icontains=search_query) |
                models.Q(store_type__name__icontains=search_query)
            )

        vendors = list(vendors)  # evaluate queryset
        vendors.sort(key=lambda v: v.is_open() or False, reverse=True)  # Open vendors first
        paginator = Paginator(vendors, 200)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context.update({
            'vendors': page_obj,
            'show_pagination': paginator.num_pages > 1,
        })
    else:
        # Start with base queryset
        products = Product.objects.filter(is_available=True, is_active=True)

        # Handle category/subcategory filter
        if subcategory_id:
            selected_subcategory = get_object_or_404(Category, id=subcategory_id, is_active=True)
            products = products.filter(subcategory=selected_subcategory)
        elif category_id:
            selected_category = get_object_or_404(Category, id=category_id, is_active=True)
            products = products.filter(category=selected_category)

        # Apply search filter
        if search_query:
            products = products.filter(
                models.Q(product_name__icontains=search_query) | 
                models.Q(product_desc__icontains=search_query)
            )

            # If no products found, try searching by category name
            if not products.exists():
                matching_categories = Category.objects.filter(
                    category_name__icontains=search_query,
                    is_active=True
                )
                if matching_categories.exists():
                    matched_category = matching_categories.first()
                    subcategories = matched_category.subcategories.all()
                    products = Product.objects.filter(
                        subcategory__in=subcategories, 
                        is_available=True, 
                        is_active=True
                    )

        # Filter by store type if provided
        if store_type:
            vendors = Vendor.objects.filter(store_type__slug=store_type, is_approved=True)
            products = products.filter(vendor__in=vendors)
        
        # Apply sorting
        if sort_type == 'dsec':
            products = products.order_by('-sales_price')
        elif sort_type == "asec":
            products = products.order_by('sales_price')
        else:
            # Default ordering to avoid pagination warning
            products = products.order_by('id')

        # Handle cart items for both authenticated and guest users
        cart_items = []
        cart_product_ids = set()

        if request.user.is_authenticated:
            for cart_obj in Cart.objects.filter(user=request.user).order_by('created_at'):
                cart_items.append({
                    'product': cart_obj.product,
                    'quantity': cart_obj.quantity,
                    'variant': cart_obj.product_variant_group,
                    'cart_id': cart_obj.id,
                    'price': cart_obj.product_variant_group.price if cart_obj.product_variant_group else cart_obj.product.sales_price,
                })
                cart_product_ids.add(cart_obj.product.id)
        else:
            cart = request.session.get('cart', {})
            
            # Separate regular products and variant products
            regular_products = {}
            variant_products = {}
            
            for cart_id, quantity in cart.items():
                if '-' in cart_id:
                    # Variant product (format: "product_id-variant_id")
                    product_id, variant_id = cart_id.split('-')
                    variant_products.setdefault(product_id, {})[variant_id] = quantity
                else:
                    # Regular product (format: "product_id")
                    regular_products[cart_id] = quantity
            
            # Convert string IDs to integers for database lookup
            product_id_ints = [int(pid) for pid in regular_products.keys()]
            product_id_ints.extend([int(pid) for pid in variant_products.keys()])
            
            # Fetch all products and variants in bulk
            products_in_cart = Product.objects.filter(id__in=product_id_ints).in_bulk()
            
            variant_ids = []
            for variant_dict in variant_products.values():
                variant_ids.extend([int(vid) for vid in variant_dict.keys()])
            variants = ProductVariantGroup.objects.filter(id__in=variant_ids).in_bulk()
            
            # Build cart items for regular products
            for product_id_str, quantity in regular_products.items():
                product_id = int(product_id_str)
                product = products_in_cart.get(product_id)
                if product:
                    cart_items.append({
                        'product': product,
                        'quantity': quantity,
                        'variant': None,
                        'cart_id': product_id_str,
                        'price': product.sales_price or product.regular_price,
                    })
                    cart_product_ids.add(product.id)
            
            # Build cart items for variant products
            for product_id_str, variant_dict in variant_products.items():
                product_id = int(product_id_str)
                product = products_in_cart.get(product_id)
                if product:
                    for variant_id_str, quantity in variant_dict.items():
                        variant_id = int(variant_id_str)
                        variant = variants.get(variant_id)
                        if variant:
                            cart_items.append({
                                'product': product,
                                'quantity': quantity,
                                'variant': variant,
                                'cart_id': f"{product_id_str}-{variant_id_str}",
                                'price': variant.price,
                            })
                            cart_product_ids.add(product.id)
                
                # Build cart items for variant products
                for product_id, variant_dict in variant_products.items():
                    product = products_in_cart.get(product_id)
                    if product:
                        for variant_id, quantity in variant_dict.items():
                            variant = variants.get(variant_id)
                            if variant:
                                cart_items.append({
                                    'product': product,
                                    'quantity': quantity,
                                    'variant': variant,
                                    'cart_id': f"{product_id}-{variant_id}",
                                    'price': variant.price,
                                })
                                cart_product_ids.add(product.id)

        # Paginate products
        paginator = Paginator(products, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context.update({
            'products': page_obj,
            'show_pagination': paginator.num_pages > 1,
            'cart_product_ids': cart_product_ids,
            'cart_items': cart_items,
            'current_category_id': category_id,
            'total_vendor_products': products,
        })

    return render(request, 'marketplace/products.html', context)

def product_search_for_vendor(request):
    query = request.GET.get("term", "")
    vendor_slug = request.GET.get("vendor", "")

    vendor = get_object_or_404(Vendor, vendor_slug=vendor_slug)
    products = Product.objects.filter(vendor=vendor, product_name__icontains=query)[:10]

    data = []
    for product in products:
        data.append({
            "name": product.product_name,
            "slug": product.slug,
            "vendor_slug": vendor.vendor_slug,
            "image": product.image.url if product.image else "",
            "price": product.sales_price,
        })

    return JsonResponse(data, safe=False)


def product_search(request):
    query = request.GET.get("term", "")

    # Check for user location
    location = get_or_set_current_location(request)
    
    if location is not None:
        pnt = GEOSGeometry('POINT(%s %s)' % location)
        vendor_qs = Vendor.objects.filter(
            user_profile__location__distance_lte=(pnt, D(km=10000)),
            is_approved=True,
            user__is_active=True).annotate( distance=Distance("user_profile__location", pnt)).order_by("distance")
    else:
        pnt = None
        vendor_qs = Vendor.objects.filter( is_approved=True,  user__is_active=True)

    # Filter vendors by search term
    vendors = vendor_qs.filter(vendor_name__icontains=query)[:10]

    # Filter products
    products = Product.objects.filter(
        Q(product_name__icontains=query) | Q(vendor__vendor_name__icontains=query)).select_related('vendor')[:10]

    return JsonResponse({
        "vendors": [
            {
                "type": "vendor",
                "name": vendor.vendor_name,
                "vendor_slug": vendor.vendor_slug,
                "image": vendor.user_profile.profile_picture.url if vendor.user_profile.profile_picture else "",
                "distance": round(vendor.distance.km, 1) if pnt else None
            }
            for vendor in vendors
        ],
        "products": [
            {
                "type": "product",
                "name": product.product_name,
                "slug": product.slug,
                "vendor_name": product.vendor.vendor_name,
                "vendor_slug": product.vendor.vendor_slug,
                "image": product.image.url if product.image else "",
                "price": str(product.sales_price),
            }
            for product in products
        ]
    })

# def add_product_to_cart(request, product_id):
#     print(request)
#     if request.user.is_authenticated:
#         if request.method == 'POST':
#             # Get the product object
#             try:
#                 product = Product.objects.get(id=product_id)
#                 vendor = product.vendor
#                 existing_products_in_cart = Cart.objects.filter(user=request.user)
#                 for single_cart_prodcut in existing_products_in_cart:
#                     if single_cart_prodcut.product.vendor != vendor:
#                         single_cart_prodcut.delete()
#             except Product.DoesNotExist:
#                 return JsonResponse({'success': False, 'message': 'Product not found.'})
             
#             # Try to parse JSON data from the request body
#             try:
#                 data = json.loads(request.body)
#                 quantity = int(data.get('quantity'))
#                 if quantity <= 0:
#                     return JsonResponse({'success': False, 'message': 'Select a valid quantity'})
#             except (json.JSONDecodeError, ValueError) as e:
#                 return JsonResponse({'success': False, 'message': 'Invalid data.'})
#              # --- Get the referer ---
#             referer = request.META.get('HTTP_REFERER', '/')

#             # Check if the product is already in the cart
#             try:
#                 cart_item = Cart.objects.get(user=request.user, product=product)
#                 existing_quantity = cart_item.quantity
#             except Cart.DoesNotExist:
#                 existing_quantity = 0

#             # Calculate the total quantity after adding the new quantity
#             total_quantity = existing_quantity + quantity

#             # Check if requested quantity exceeds available stock
#             if total_quantity > product.qty:
#                 messages.warning(request, f"Only {product.qty} units of {product.product_name} are available. ")
#                 return JsonResponse({
#                     'success': True,
#                     'status':'stock_out',
#                     'message': f"Only {product.qty} units of {product.product_name} are available. ",
#                    'redirect_url': referer  
#                 })
             
#             try:
#                 cart_item = Cart.objects.get(user=request.user, product=product)
#                 cart_item.quantity += quantity
#                 cart_item.save()
#                 message = f"The quantity of {product.product_name} has been updated in your cart."
#                 messages.success(request, f"The quantity of {product.product_name} has been updated in your cart.")
#             except:
#                 cart_item = Cart.objects.create(user=request.user, product=product, quantity=quantity)
#                 # product.qty = product.qty - quantity
#                 # product.save()
#                 messages.success(request, f"{product.product_name} has been added to your cart.")
#                 message = f"{product.product_name} has been added to your cart."
            

#             return JsonResponse({
#                 'success': True,
#                 'message': message,
#                 'redirect_url': referer
#             })
        
    
#         return JsonResponse({'success': False, 'status':'invalid_method','message': 'Invalid request method.'})
           
#     else:
#         return JsonResponse({'success': False, 'status': 'login_required', 'message': 'Please login to continue'})

def add_product_to_cart(request, product_id):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            product = Product.objects.get(id=product_id)
            vendor = product.vendor
        except Product.DoesNotExist:
            return JsonResponse({'status': 'Failed', 'message': 'This product does not exist!'})

    try:
        print("data ===> ", request.body)
        data = json.loads(request.body)
        quantity = int(data.get('quantity'))
        if quantity <= 0:
            return JsonResponse({'success': False, 'message': 'Select a valid quantity'})
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'success': False, 'message': 'Invalid data.'})

    referer = request.META.get('HTTP_REFERER', '/')
    try:
        product = Product.objects.get(id=product_id)
        vendor = product.vendor
    except Product.DoesNotExist:
            return JsonResponse({'status': 'Failed', 'message': 'This product does not exist!'})

    # --- Authenticated user logic ---
    if request.user.is_authenticated:
        # Check if product is already in cart
        try:
            cart_item = Cart.objects.get(user=request.user, product=product)
            existing_quantity = cart_item.quantity
            cart_item_exists = True
        except Cart.DoesNotExist:
            existing_quantity = 0
            cart_item_exists = False

        total_quantity = existing_quantity + quantity

        # Stock check
        if total_quantity > product.qty:
            return JsonResponse({
                'success': True,
                'status': 'stock_out',
                'message': f"Only {int(product.qty)} units of {product.product_name} are available.",
                'redirect_url': referer
            })

        if cart_item_exists:
            cart_item.quantity = total_quantity
            cart_item.save()
            message = f"The quantity of {product.product_name} has been updated in your cart."
        else:
            cart_item = Cart.objects.create(user=request.user, product=product, quantity=quantity)
            message = f"{product.product_name} has been added to your cart."
        cart_counter = get_cart_counter(request)
        chkCart_count = cart_item.quantity
        print("chkCart_count ===> ", chkCart_count)
        return JsonResponse({
            'success': True,
            'cart_counter': cart_counter['cart_count'],
            'chkCart_count':chkCart_count,
            'redirect_url': referer
        })

    # --- Guest user (session cart) logic ---
    else:
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)
        
        # Check if we have variant data
        variant_data = data.get('variants', {})
        variant_group = None
        
        if variant_data:
            variant_group = get_matching_variant_group(product, variant_data)
        
        # Create appropriate cart key
        if variant_group:
            cart_id = f"{product_id_str}-{variant_group.id}"
        else:
            cart_id = product_id_str
        
        existing_quantity = int(cart.get(cart_id, 0))
        total_quantity = existing_quantity + quantity

        # Stock check
        available_qty = variant_group.stock if variant_group else product.qty
        if total_quantity > available_qty:
            return JsonResponse({
                'success': True,
                'status': 'stock_out',
                'message': f"Only {available_qty} units are available.",
                'redirect_url': referer
            })

        cart[cart_id] = total_quantity
        request.session['cart'] = cart
        request.session.modified = True

        if existing_quantity == 0:
            message = f"{product.product_name} has been added to your cart."
        else:
            message = f"The quantity has been updated in your cart."
        
        return JsonResponse({
            'success': True,
            'message': message,
            'cart_counter': sum(int(q) for q in cart.values()),
            'redirect_url': referer,
            'chkCart_count': total_quantity,
        })



def categories(request):
    categories = Category.objects.filter(parent__isnull=True, is_active=True).prefetch_related('subcategories').distinct()
    context = {'categories': categories}
    return render(request, 'marketplace/categories.html', context)


def browse(request, category_slug):
    try:
        browse_page = CategoryBrowsePage.objects.select_related('category').prefetch_related(
            'sections__products__product',
            'sections__subcategories__subcategory',
        ).get(category__slug=category_slug)
        sections = browse_page.sections.all()
    except CategoryBrowsePage.DoesNotExist:
        return  redirect('filter_by_category', category_id=Category.objects.get(slug=category_slug).id)
    
    if request.user.is_authenticated:
        cart_items = []
        for cart_obj in Cart.objects.filter(user=request.user).order_by('created_at'):
            cart_items.append({
                'product': cart_obj.product,
                'quantity': cart_obj.quantity,
                'cart_id': cart_obj.id,  # DB cart uses Cart PK
            })
    else:
        cart = request.session.get('cart', {})
        cart_items = []
        
        # Separate regular products and variant products
        regular_products = {}
        variant_products = {}
        
        for cart_id, quantity in cart.items():
            if '-' in cart_id:
                # Variant product (format: "product_id-variant_id")
                product_id, variant_id = cart_id.split('-')
                variant_products.setdefault(product_id, {})[variant_id] = quantity
            else:
                # Regular product (format: "product_id")
                regular_products[cart_id] = quantity
        
        # Convert string IDs to integers for database lookup
        product_id_ints = [int(pid) for pid in regular_products.keys()]
        product_id_ints.extend([int(pid) for pid in variant_products.keys()])
        
        # Fetch all products and variants in bulk
        products = Product.objects.filter(id__in=product_id_ints).in_bulk()
        
        variant_ids = [int(vid) for vid_dict in variant_products.values() for vid in vid_dict.keys()]
        variants = ProductVariantGroup.objects.filter(id__in=variant_ids).in_bulk()
        
        # Build cart items for regular products
        for product_id_str, quantity in regular_products.items():
            product_id = int(product_id_str)
            product = products.get(product_id)
            if product:
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'variant': None,
                    'cart_id': product_id_str,  # Keep original string ID for session
                    'price': product.sales_price or product.regular_price,
                })
        
        # Build cart items for variant products
        for product_id_str, variant_dict in variant_products.items():
            product_id = int(product_id_str)
            product = products.get(product_id)
            if product:
                for variant_id_str, quantity in variant_dict.items():
                    variant_id = int(variant_id_str)
                    variant = variants.get(variant_id)
                    if variant:
                        cart_items.append({
                            'product': product,
                            'quantity': quantity,
                            'variant': variant,
                            'cart_id': f"{product_id_str}-{variant_id_str}",
                            'price': variant.price,
                        })

    # Get product IDs
    cart_product_ids = set()
    for item in cart_items:
        if isinstance(item, dict) and 'product' in item and item['product']:
            cart_product_ids.add(item['product'].id)
        elif hasattr(item, 'product') and item.product:  # For model instances
            cart_product_ids.add(item.product.id)

    print("cart_items", cart_items)
    print("cart_product_ids", cart_product_ids)
    context = {
        'page': browse_page,
        'sections': sections ,
        'cart_items': cart_items,
        'cart_product_ids': cart_product_ids,
    }
    
    return render(request, 'marketplace/browse.html', context)