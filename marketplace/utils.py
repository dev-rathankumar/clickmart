from unified.models import Product
from .models import Cart

def merge_session_cart_to_db(request, user):
    session_cart = request.session.get('cart', {})
    for product_id, qty in session_cart.items():
        try:
            product = Product.objects.get(id=product_id)
            # Check if the user already has this product in their DB cart
            try:
                cart_item = Cart.objects.get(user=user, product=product)
            except Cart.DoesNotExist:
                created = Cart.objects.create(user=user, product=product, quantity=qty)
                continue
            cart_item.quantity = min(int(qty), int(product.qty))
            cart_item.save()
        except Product.DoesNotExist:
            continue  # If product doesn't exist, skip it
    # Clear the session cart after merging
    request.session['cart'] = {}
    request.session.modified = True