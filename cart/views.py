# Create your views here.
from django.shortcuts import redirect
# from inventory.models import product as Product
from unified.models import Product
from django.contrib.auth.decorators import login_required

from vendor.models import Vendor
from .models import Cart


# @login_required(login_url="/pos/user/login")
# def cart_add(request,id,qty):
#     print("type qty", qty)

#     cart = Cart(request)
#     vendor = Vendor.objects.get(user=request.user)
#     product = Product.objects.filter(id=id, vendor=vendor).first()
#     print(cart)
#     for key in cart:
#         print(key)

#     if product:
#         if product.qty >= int(qty):
#             cart.add(product=product,quantity=int(qty))
#             return redirect('register')
#         else:
#             scheme = request.is_secure() and "https" or "http"
#             return redirect(f"{scheme}://{request.get_host()}/pos/register/NotEnoughQTY/")
        
#     else:
#         scheme = request.is_secure() and "https" or "http"
#         return redirect(f"{scheme}://{request.get_host()}/pos/register/ProductNotFound/")

@login_required(login_url="/pos/user/login")
def cart_add(request, id, qty):
    print("type qty", qty)

    cart = Cart(request)  # Custom Cart instance
    vendor = Vendor.objects.get(user=request.user)
    product = Product.objects.filter(id=id, vendor=vendor).first()
    print(cart)

    if not product:
        scheme = request.is_secure() and "https" or "http"
        return redirect(f"{scheme}://{request.get_host()}/pos/register/ProductNotFound/")

    # Check if the product exists in the cart
    product_in_cart = None
    for item in cart.get_items():  # Call `get_items()` to get all items
        if item['product_id'] == str(product.id):  # Compare product ID
            product_in_cart = item
            break

    # Calculate the new total quantity
    new_total_qty = int(qty)
    if product_in_cart:
        new_total_qty += product_in_cart['quantity']

    # Check stock availability
    if new_total_qty > product.qty:
        scheme = request.is_secure() and "https" or "http"
        return redirect(f"{scheme}://{request.get_host()}/pos/register/NotEnoughQTY/")

    # Add or update product in the cart
    cart.add(product=product, quantity=int(qty))
    return redirect('register')

@login_required(login_url="/pos/user/login")
def item_clear(request, id):
    cart = Cart(request)
    product = Product.objects.get(barcode=id)
    cart.remove(product)
    return redirect("cart_detail")


@login_required(login_url="/pos/user/login")
def item_increment(request, id):
    cart = Cart(request)
    product = Product.objects.get(barcode=id)
    cart.add(product=product)
    return redirect("cart_detail")


@login_required(login_url="/pos/user/login")
def item_decrement(request, id):
    cart = Cart(request)
    product = Product.objects.get(barcode=id)
    cart.decrement(product=product)
    return redirect("cart_detail")


@login_required(login_url="/pos/user/login")
def cart_clear(request):
    cart = Cart(request)
    cart.clear()
    return redirect('register')

