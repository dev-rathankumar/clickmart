from unified.models import Product, ProductVariantGroup, VariantAttributeValue
from .models import Cart
from django.db.models import Count
def merge_session_cart_to_db(request, user):
    session_cart = request.session.get('cart', {})
    
    for cart_key, qty in session_cart.items():
        try:
            # Check if this is a variant product (has hyphen in key)
            if '-' in cart_key:
                # Variant product (format: "product_id-variant_id")
                product_id, variant_id = cart_key.split('-')
                try:
                    product = Product.objects.get(id=product_id)
                    variant = ProductVariantGroup.objects.get(id=variant_id, product=product)
                    
                    # Check if user already has this product+variant in cart
                    try:
                        cart_item = Cart.objects.get(
                            user=user, 
                            product=product, 
                            product_variant_group=variant
                        )
                        # Update quantity, respecting stock limits
                        available_qty = variant.stock
                        new_qty = min(int(qty), available_qty)
                        if new_qty > 0:
                            cart_item.quantity = new_qty
                            cart_item.save()
                        else:
                            cart_item.delete()
                    except Cart.DoesNotExist:
                        # Only create if we have available stock
                        available_qty = variant.stock
                        if available_qty > 0:
                            Cart.objects.create(
                                user=user,
                                product=product,
                                product_variant_group=variant,
                                quantity=min(int(qty), available_qty))
                except (Product.DoesNotExist, ProductVariantGroup.DoesNotExist):
                    continue
            else:
                # Regular product
                product = Product.objects.get(id=cart_key)
                
                # Check if user already has this product in cart
                try:
                    cart_item = Cart.objects.get(
                        user=user, 
                        product=product,
                        product_variant_group__isnull=True
                    )
                    # Update quantity, respecting stock limits
                    available_qty = product.qty
                    new_qty = min(int(qty), available_qty)
                    if new_qty > 0:
                        cart_item.quantity = new_qty
                        cart_item.save()
                    else:
                        cart_item.delete()
                except Cart.DoesNotExist:
                    # Only create if we have available stock
                    available_qty = product.qty
                    if available_qty > 0:
                        Cart.objects.create(
                            user=user,
                            product=product,
                            quantity=min(int(qty), available_qty))
        except Product.DoesNotExist:
            continue  # Skip if product doesn't exist
    
    # Clear the session cart after merging
    request.session['cart'] = {}
    request.session.modified = True

def get_matching_variant_group(product, variant_data):
    # Step 1: Convert IDs in variant_data to a list of VariantAttributeValue objects
    try:
        value_ids = [int(v) for v in variant_data.values()]
    except ValueError:
        return None  # Invalid ID in variant data

    # Step 2: Try to fetch the VariantAttributeValue objects
    variant_values = VariantAttributeValue.objects.filter(id__in=value_ids, product=product)

    # Optional check: ensure we have all values (avoid partial match)
    if variant_values.count() != len(value_ids):
        return None  # One or more invalid/missing values

    # Step 3: Query the ProductVariantGroup that has exactly the same attribute set
    # Match: same number of attributes, all IDs must match, no extra
    matching_variant_group = (
        ProductVariantGroup.objects
        .filter(product=product, attribute__in=variant_values)
        .annotate(num_attrs=Count('attribute'))
        .filter(num_attrs=len(value_ids))
        .distinct()
        .first()
    )

    return matching_variant_group



# In your view or wherever you're generating the variant combinations:
def get_variant_combinations(product):
    variant_groups = ProductVariantGroup.objects.filter(product=product).select_related('product').prefetch_related('attribute')
    
    variant_combinations = [
        {
            "group_id": group.id,
            "attributes": [str(attr.id) for attr in group.attribute.all()],
            "price": float(group.price) if group.price else None,
            "stock": float(group.stock) if group.stock is not None else 0,
            "in_stock": group.in_stock,
            "image": group.image.url if group.image else None,
            "sku": group.sku
        }
        for group in variant_groups
    ]
    return variant_combinations