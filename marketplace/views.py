from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import UserProfile
from .context_processors import get_cart_counter, get_cart_amounts
from unified.models import Category, ProductGallery

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



def marketplace(request):
    vendors = Vendor.objects.filter(is_approved=True, user__is_active=True)
    vendor_count = vendors.count()
    context = {
        'vendors': vendors,
        'vendor_count': vendor_count,
    }
    return render(request, 'marketplace/listings.html', context)

def vendor_detail(request, vendor_slug, category_id=None, subcategory_id=None):
    vendor = get_object_or_404(Vendor, vendor_slug=vendor_slug)
    categories = Category.objects.filter(is_active=True, parent=None, vendor=vendor).prefetch_related('subcategories')

    # Handle search query
    search_query = request.GET.get('search', None)

    if subcategory_id:
        # Filter by subcategory
        selected_subcategory = get_object_or_404(Category, id=subcategory_id, is_active=True, vendor=vendor)
        products = Product.objects.filter(
            subcategory=selected_subcategory, 
            is_available=True, 
            is_active=True, 
            vendor=vendor
        )
    elif category_id:
        # Filter by category
        selected_category = get_object_or_404(Category, id=category_id, is_active=True, vendor=vendor)
        subcategories = selected_category.subcategories.all()
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

    opening_hours = OpeningHour.objects.filter(vendor=vendor).order_by('day', 'from_hour')
    today_date = date.today()
    today = today_date.isoweekday()
    current_opening_hours = OpeningHour.objects.filter(vendor=vendor, day=today)
    
    cart_items = Cart.objects.filter(user=request.user) if request.user.is_authenticated else None
    
    context = {
        'vendor': vendor,
        'categories': categories,
        'cart_items': cart_items,
        'opening_hours': opening_hours,
        'current_opening_hours': current_opening_hours,
        'products': products,
        'search_query': search_query  # Pass the search query to template
    }
    return render(request, 'marketplace/vendor_detail.html', context)


def view_Product(request, vendor_slug, product_slug):
    # Get the main product
    product = get_object_or_404(Product, vendor__vendor_slug=vendor_slug, slug=product_slug)
    if request.user.is_authenticated:
        chkCart = Cart.objects.filter(product=product, user=request.user)
        chkCart_count = chkCart.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
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
        'product': product,
        'similar_products': similar_products,
        'check_cart':chkCart,
        'chkCart_count':chkCart_count,
        'product_gallery':product_gallery
    }
    
    return render(request, 'vendor/product_view.html', context)


def add_to_cart(request, food_id):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Check if the food item exists
            try:
                product = Product.objects.get(id=food_id)

                # Check if the user has already added that food to the cart
                try:
                    chkCart = Cart.objects.get(user=request.user, product=product)
                    
                    # Calculate the new quantity after increment
                    new_quantity = chkCart.quantity + 1
                    
                    # Check if the new quantity exceeds available stock
                    if new_quantity > product.qty:
                        return JsonResponse({
                            'status': 'Failed',
                            'message': f'Only {product.qty} units of {product.product_name} are available in stock.',
                            'cart_counter': get_cart_counter(request),
                            'qty': chkCart.quantity,
                            'cart_amount': get_cart_amounts(request)
                        })

                    # Increase the cart quantity
                    chkCart.quantity = new_quantity
                    chkCart.save()
                    return JsonResponse({
                        'status': 'Success',
                        'message': 'Increased the cart quantity',
                        'cart_counter': get_cart_counter(request),
                        'qty': chkCart.quantity,
                        'cart_amount': get_cart_amounts(request)
                    })
                except Cart.DoesNotExist:
                    # Check if stock is available for at least one unit
                    if product.qty < 1:
                        return JsonResponse({
                            'status': 'Failed',
                            'message': f'{product.product_name} is out of stock.',
                            'cart_counter': get_cart_counter(request),
                            'qty': 0,
                            'cart_amount': get_cart_amounts(request)
                        })

                    # Add the product to the cart with a quantity of 1
                    chkCart = Cart.objects.create(user=request.user, product=product, quantity=1)
                    return JsonResponse({
                        'status': 'Success',
                        'message': 'Added the product to the cart',
                        'cart_counter': get_cart_counter(request),
                        'qty': chkCart.quantity,
                        'cart_amount': get_cart_amounts(request)
                    })
            except Product.DoesNotExist:
                return JsonResponse({'status': 'Failed', 'message': 'This product does not exist!'})
        else:
            return JsonResponse({'status': 'Failed', 'message': 'Invalid request!'})
    else:
        return JsonResponse({'status': 'login_required', 'message': 'Please login to continue'})


def decrease_cart(request, food_id):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Check if the food item exists
            try:
                product = Product.objects.get(id=food_id)
                # Check if the user has already added that food to the cart
                try:
                    chkCart = Cart.objects.get(user=request.user, product=product)
                    if chkCart.quantity > 1:
                        # decrease the cart quantity
                        chkCart.quantity -= 1
                        # product.qty += 1 
                        # product.save()
                        chkCart.save()
                    else:
                        # product.qty += 1 
                        # product.save()
                        chkCart.delete()
                        chkCart.quantity = 0
                    return JsonResponse({'status': 'Success', 'cart_counter': get_cart_counter(request), 'qty': chkCart.quantity, 'cart_amount': get_cart_amounts(request)})
                except:
                    return JsonResponse({'status': 'Failed', 'message': 'You do not have this item in your cart!'})
            except:
                return JsonResponse({'status': 'Failed', 'message': 'This food does not exist!'})
        else:
            return JsonResponse({'status': 'Failed', 'message': 'Invalid request!'})
        
    else:
        return JsonResponse({'status': 'login_required', 'message': 'Please login to continue'})


@login_required(login_url = 'login')
def cart(request):
    cart_items = Cart.objects.filter(user=request.user).order_by('created_at')
    context = {
        'cart_items': cart_items,
    }
    return render(request, 'marketplace/cart.html', context)


def delete_cart(request, cart_id):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                # Check if the cart item exists
                cart_item = Cart.objects.get(user=request.user, id=cart_id)
                if cart_item:
                    product = Product.objects.get(id=cart_item.product.id)
                    # product.qty +=cart_item.quantity
                    # product.save()
                    cart_item.delete()
                    return JsonResponse({'status': 'Success', 'message': 'Cart item has been deleted!', 'cart_counter': get_cart_counter(request), 'cart_amount': get_cart_amounts(request)})
            except:
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
        fetch_vendors_by_products = Product.objects.filter(food_title__icontains=keyword, is_available=True).values_list('vendor', flat=True)
        
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
    categories = Category.objects.filter(is_active=True, parent=None).prefetch_related('subcategories')
    
    if subcategory_id:
        # Filter by subcategory
        selected_subcategory = get_object_or_404(Category, id=subcategory_id, is_active=True)
        print("selecterd category", selected_subcategory)
        products = Product.objects.filter(subcategory=selected_subcategory, is_available=True, is_active=True)
        print(products)

    elif category_id:
        # Filter by category
        selected_category = get_object_or_404(Category, id=category_id, is_active=True)
        subcategories = selected_category.subcategories.all()
        products = Product.objects.filter(subcategory__in=subcategories, is_available=True, is_active=True)
    else:
        # Show all products if no filter is selected
        products = Product.objects.filter(is_available=True, is_active=True)
    print(products)
    context = {
        'categories': categories,
        'products': products,
    }
    return render(request, 'marketplace/products.html', context)

def add_product_to_cart(request, product_id):
    print(request)
    if request.user.is_authenticated:
        if request.method == 'POST':
            # Get the product object
            try:
                product = Product.objects.get(id=product_id)
                vendor = product.vendor
                existing_products_in_cart = Cart.objects.filter(user=request.user)
                for single_cart_prodcut in existing_products_in_cart:
                    if single_cart_prodcut.product.vendor != vendor:
                        single_cart_prodcut.delete()
            except Product.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Product not found.'})
             
            # Try to parse JSON data from the request body
            try:
                data = json.loads(request.body)
                quantity = int(data.get('quantity'))
            except (json.JSONDecodeError, ValueError) as e:
                return JsonResponse({'success': False, 'message': 'Invalid data.'})
            
            # Check if the product is already in the cart
            try:
                cart_item = Cart.objects.get(user=request.user, product=product)
                existing_quantity = cart_item.quantity
            except Cart.DoesNotExist:
                existing_quantity = 0

            # Calculate the total quantity after adding the new quantity
            total_quantity = existing_quantity + quantity

            # Check if requested quantity exceeds available stock
            if total_quantity > product.qty:
                messages.warning(request, f"Only {product.qty} units of {product.product_name} are available. ")
                return JsonResponse({
                    'success': True,
                    'status':'stock_out',
                    'message': f"Only {product.qty} units of {product.product_name} are available. ",
                    'redirect_url': f'/marketplace/product/{product.vendor.vendor_slug}/{product.slug}/'
                })
             
            try:
                cart_item = Cart.objects.get(user=request.user, product=product)
                cart_item.quantity += quantity
                cart_item.save()
                message = f"The quantity of {product.product_name} has been updated in your cart."
            except:
                cart_item = Cart.objects.create(user=request.user, product=product, quantity=quantity)
                # product.qty = product.qty - quantity
                # product.save()
                messages.success(request, f"{product.product_name} has been added to your cart.")
                message = f"{product.product_name} has been added to your cart."
            

            return JsonResponse({
                'success': True,
                'message': message,
                'redirect_url': f'/marketplace/product/{product.vendor.vendor_slug}/{product.slug}/'  # Redirect to the cart page or any other page
            })
        
    
        return JsonResponse({'success': False, 'status':'invalid_method','message': 'Invalid request method.'})
           
    else:
        return JsonResponse({'status': 'login_required', 'message': 'Please login to continue'})


def categories(request):
    categories = Category.objects.filter(parent__isnull=True, is_active=True).prefetch_related('subcategories').distinct()
    context = {'categories': categories}
    return render(request, 'marketplace/categories.html', context)