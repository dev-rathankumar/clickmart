from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import UserProfile, DeliveryAddress
from .context_processors import get_cart_counter, get_cart_amounts
from unified.models import Category, CategoryBrowsePage, ProductGallery

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


def marketplace(request):
    vendors = Vendor.objects.filter(is_approved=True, user__is_active=True)
    vendor_count = vendors.count()

    search_query = request.GET.get('search', None)
    
    if search_query:
        vendors = vendors.filter(
            Q(vendor_name__icontains=search_query) |
            Q(vendor_slug__icontains=search_query) |
            Q(store_type__name__icontains=search_query)
        )

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
    categories = Category.objects.filter(is_active=True, parent=None, store_type=vendor.store_type).prefetch_related('subcategories')

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
        subcategories = selected_category.subcategories.filter(vendor_subcategory_reference_id=vendor.id)
        products = Product.objects.filter(
            subcategory__in=subcategories, 
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

    context = {
        'vendor': vendor,
        'categories': categories,
        'cart_items': cart_items,
        'opening_hours': opening_hours,
        'current_opening_hours': current_opening_hours,
        'products': page_obj,
        'search_query': search_query, 
        'show_pagination':show_pagination

    }
    return render(request, 'marketplace/vendor_detail.html', context)


def view_Product(request, vendor_slug, product_slug):
    # Get the main product
    product = get_object_or_404(Product, vendor__vendor_slug=vendor_slug, slug=product_slug)
    if request.user.is_authenticated:
        address = DeliveryAddress.objects.filter(user=request.user, is_primary=True).first()
    else:
        address=None
    vendor = Vendor.objects.get(vendor_slug=vendor_slug)
    # Vendor distance 
    if get_or_set_current_location(request) is not None:

        pnt = GEOSGeometry('POINT(%s %s)' % (get_or_set_current_location(request)))

        vendors = Vendor.objects.filter(user_profile__location__distance_lte=(pnt, D(km=100000))).annotate(distance=Distance("user_profile__location", pnt)).order_by("distance")
        print("vendros ===> ", vendors)
        for v in vendors:
            if v.id == vendor.id: 
                vendor.kms = round(v.distance.km, 1)


    different_vendor_product_exists=False
    if request.user.is_authenticated:
        chkCart = Cart.objects.filter(product=product, user=request.user)
        existing_products_in_cart = Cart.objects.filter(user=request.user)
        for single_cart_prodcut in existing_products_in_cart:
            if single_cart_prodcut.product.vendor != vendor:
                different_vendor_product_exists=True
        chkCart_count = chkCart.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
    else:
        product_id_str = str(product.id)
        cart = request.session.get('cart', {})
        if product_id_str in cart:
            chkCart = True
            chkCart_count = cart[product_id_str]
        else:
            chkCart = None
            chkCart_count = 0
    product_gallery = ProductGallery.objects.filter(product=product)
    # Fetch similar products from the same category, excluding the current product
    similar_products = Product.objects.filter(
        category=product.category,
        is_available=True  # Optional: Only include available products
    ).exclude(id=product.id)
    
    context = {
        'vendor':vendor,
        'product': product,
        'similar_products': similar_products,
        'check_cart':chkCart,
        'chkCart_count':chkCart_count,
        'product_gallery':product_gallery,
        'different_vendor_product_exists':different_vendor_product_exists,
        'address':address
    }
    
    return render(request, 'vendor/product_view.html', context)

def add_to_cart(request, food_id):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            product = Product.objects.get(id=food_id)
        except Product.DoesNotExist:
            return JsonResponse({'status': 'Failed', 'message': 'This product does not exist!'})

        # --- Authenticated user ---
        if request.user.is_authenticated:
            try:
                chkCart = Cart.objects.get(user=request.user, product=product)
                new_quantity = chkCart.quantity + 1
                if new_quantity > product.qty:
                    cart_counter = get_cart_counter(request)
                    return JsonResponse({
                        'status': 'Failed',
                        'message': f'Only {product.qty} units of {product.product_name} are available in stock.',
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
                    'cart_amount': get_cart_amounts(request)
                })
            except Cart.DoesNotExist:
                if product.qty < 1:
                    cart_counter = get_cart_counter(request)
                    return JsonResponse({
                        'status': 'Failed',
                        'message': f'{product.product_name} is out of stock.',
                        'cart_counter':cart_counter['cart_count'],
                        'qty': 0,
                        'cart_amount': get_cart_amounts(request)
                    })
                chkCart = Cart.objects.create(user=request.user, product=product, quantity=1)
                cart_counter = get_cart_counter(request)
                return JsonResponse({
                    'status': 'Success',
                    'message': 'Added the product to the cart',
                    'cart_counter': cart_counter['cart_count'],
                    'qty': chkCart.quantity,
                    'cart_amount': get_cart_amounts(request)
                })

        # --- Guest user (session cart) ---
        else:
            cart = request.session.get('cart', {})
            product_id = str(product.id)
            prev_qty = int(cart.get(product_id, 0))
            new_qty = prev_qty + 1

            if new_qty > product.qty:
                return JsonResponse({
                    'status': 'Failed',
                    'message': f'Only {product.qty} units of {product.product_name} are available in stock.',
                    'cart_counter': sum(cart.values()),
                    'qty': prev_qty,
                    'cart_amount': get_cart_amounts(request, session_cart=cart)
                })

            cart[product_id] = new_qty
            request.session['cart'] = cart
            request.session.modified = True

            return JsonResponse({
                'status': 'Success',
                'message': 'Added the product to the cart',
                'cart_counter': sum(cart.values()),
                'qty': cart[product_id],
                'cart_amount': get_cart_amounts(request, session_cart=cart)
            })
    else:
        return JsonResponse({'status': 'Failed', 'message': 'Invalid request!'})
    


def decrease_cart(request, food_id):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            product = Product.objects.get(id=food_id)
        except Product.DoesNotExist:
            return JsonResponse({'status': 'Failed', 'message': 'This product does not exist!'})

        if request.user.is_authenticated:
            try:
                chkCart = Cart.objects.get(user=request.user, product=product)
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
                    'cart_amount': get_cart_amounts(request)
                })
            except Cart.DoesNotExist:
                return JsonResponse({'status': 'Failed', 'message': 'You do not have this item in your cart!'})
        else:
            cart = request.session.get('cart', {})
            product_id = str(product.id)
            qty = int(cart.get(product_id, 0))
            if qty > 1:
                cart[product_id] = qty - 1
                new_qty = cart[product_id]
            elif qty == 1:
                del cart[product_id]
                new_qty = 0
            else:
                return JsonResponse({'status': 'Failed', 'message': 'You do not have this item in your cart!'})
            request.session['cart'] = cart
            request.session.modified = True
            return JsonResponse({
                'status': 'Success',
                'cart_counter': sum(cart.values()),
                'qty': new_qty,
                'cart_amount': get_cart_amounts(request, session_cart=cart)
            })
    else:
        return JsonResponse({'status': 'Failed', 'message': 'Invalid request!'})
    

def cart(request):
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
        product_ids = list(cart.keys())
        products = Product.objects.filter(id__in=product_ids)
        cart_items = []
        for product in products:
            cart_items.append({
                'product': product,
                'quantity': cart[str(product.id)],
                'cart_id': product.id,  # session cart uses product id
            })

            print("cart_items ===> ", cart_items)
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
                print("cart_id ===> ", cart_id)
                print("cart ---> ", Cart.objects.filter(user=request.user) )
                cart_item = Cart.objects.get(user=request.user, id=cart_id)
                cart_item.delete()
                cart_counter = get_cart_counter(request)
                return JsonResponse({
                    'status': 'Success',
                    'message': 'Cart item has been deleted!',
                    'cart_counter':cart_counter['cart_count'],
                    'cart_amount': get_cart_amounts(request)
                })
            except Cart.DoesNotExist:
                return JsonResponse({'status': 'Failed', 'message': 'Cart Item does not exist!'})
        # Guest user: remove from session cart
        else:
            cart = request.session.get('cart', {})
            product_id = str(cart_id)
            if product_id in cart:
                del cart[product_id]
                request.session['cart'] = cart
                request.session.modified = True
                
                return JsonResponse({
                    'status': 'Success',
                    'message': 'Cart item has been deleted!',
                    'cart_counter': sum(cart.values()),
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
            ).annotate(distance=Distance("user_profile__location", pnt)).order_by("distance")

            for v in vendors:
                v.kms = round(v.distance.km, 1)
        vendor_count = vendors.count()
        context = {
            'vendors': vendors,
            'vendor_count': vendor_count,
            'source_location': address,
        }


        return render(request, 'marketplace/listings.html', context)



@login_required(login_url='login')
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

    # ---- Initialize context here ----
    context = {
        'categories': categories,
        'search_type': search_type,
        'search_query': search_query,
    }

    if search_type == 'stores':
        if get_or_set_current_location(request) is not None:

            pnt = GEOSGeometry('POINT(%s %s)' % (get_or_set_current_location(request)))

            vendors = Vendor.objects.filter(user_profile__location__distance_lte=(pnt, D(km=10000))).annotate(distance=Distance("user_profile__location", pnt)).order_by("distance")

            for v in vendors:
                v.kms = round(v.distance.km, 1)
        else:
            vendors = Vendor.objects.filter(is_approved=True, user__is_active=True)
        
        print("vendors ===> ", vendors)

        if search_query:
            vendors = vendors.filter(
                models.Q(vendor_name__icontains=search_query) |
                models.Q(store_type__name__icontains=search_query)
            )
        paginator = Paginator(vendors, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context.update({
            'vendors': page_obj,
            'show_pagination': paginator.num_pages > 1,
        })
    else:
        products = Product.objects.filter(is_available=True, is_active=True)

        # Handle category/subcategory filter
        if subcategory_id:
            selected_subcategory = get_object_or_404(Category, id=subcategory_id, is_active=True)
            products = products.filter(subcategory=selected_subcategory)
        elif category_id:
            selected_category = get_object_or_404(Category, id=category_id, is_active=True)
            subcategories = selected_category.subcategories.all()
            products = products.filter(subcategory__in=subcategories)

        # If not category search, filter by product name/desc as usual
        if search_query:
            products = products.filter(
                models.Q(product_name__icontains=search_query) | models.Q(product_desc__icontains=search_query)
            )

        # Handle search by category name
        if search_query and products.count() <= 0:
            # Try to find a matching category (case-insensitive, partial match)
            matching_categories = Category.objects.filter(
                category_name__icontains=search_query,
                is_active=True
            )
            if matching_categories.exists():
                matched_category = matching_categories.first()
                subcategories = matched_category.subcategories.all()
                products = Product.objects.filter(subcategory__in=subcategories, is_available=True, is_active=True)

        # Filter by store type if provided
        if store_type:
            vendors = Vendor.objects.filter(store_type__slug=store_type, is_approved=True)
            products = products.filter(vendor__in=vendors)
        
        if sort_type == 'dsec':
            products = products.order_by('-sales_price')
        if sort_type == "asec":
            products = products.order_by('sales_price')
        user_cart = Cart.objects.filter(user=request.user) if request.user.is_authenticated else []
        cart_vendors = set(item.product.vendor_id for item in user_cart)

        for product in products:
            # True if cart is not empty and this product's vendor is NOT in the cart's vendors
            product.is_different_vendor_for_cart = bool(cart_vendors) and (product.vendor_id not in cart_vendors)

        paginator = Paginator(products, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context.update({
            'products': page_obj,
            'show_pagination': paginator.num_pages > 1,
        })

    return render(request, 'marketplace/products.html', context)

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
        existing_quantity = int(cart.get(product_id_str, 0))
        total_quantity = existing_quantity + quantity

        # Stock check
        if total_quantity > product.qty:
            return JsonResponse({
                'success': True,
                'status': 'stock_out',
                'message': f"Only {product.qty} units of {product.product_name} are available.",
                'redirect_url': referer
            })

        cart[product_id_str] = total_quantity
        request.session['cart'] = cart
        request.session.modified = True

        if existing_quantity == 0:
            message = f"{product.product_name} has been added to your cart."
        else:
            message = f"The quantity of {product.product_name} has been updated in your cart."
        chkCart_count = total_quantity

        return JsonResponse({
            'success': True,
            'message': message,
            'cart_counter': sum(cart.values()),
            'redirect_url': referer,
            'chkCart_count':chkCart_count,

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
        product_ids = list(cart.keys())
        cart_products  = Product.objects.filter(id__in=product_ids)
        cart_items = []
        for product in cart_products :
            print("product_id ===>", product.id)
            quantity = cart.get(str(product.id))
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'cart_id': product.id,  # session cart uses product id
            })
    print("cart_items", type(cart_items))
    cart_product_ids = set(item['product'].id for item in cart_items)
    print("cart_product_ids", cart_product_ids)
    print("sections ===> ", sections)
    print("browse_page ===> ", browse_page)
    context = {
        'page': browse_page,
        'sections': sections ,
        'cart_items': cart_items,
        'cart_product_ids': cart_product_ids,
    }
    
    return render(request, 'marketplace/browse.html', context)