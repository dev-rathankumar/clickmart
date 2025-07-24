from django.db import transaction
from django.core.exceptions import ValidationError
from unified.models import ProductAttribute, ProductAttributeValue, VariantAttribute,VariantAttributeValue,ProductVariantGroup
from decimal import Decimal, InvalidOperation
import decimal
from django.db import models

def save_product_attributes(product_obj, attribute_str, vendor):
    """
    Save ProductAttribute and ProductAttributeValue for a product.
    - attribute_str: "Material:Plastic;Brand:Rolex;Quantity:25ML,50ML,100ML"
    """
    if not attribute_str:
        return

    # Split by semicolon to get each attribute (key:value)
    attributes = [item.strip() for item in attribute_str.split(';') if item.strip()]
    for attr in attributes:
        if ':' not in attr:
            continue  # Skip malformed

        attr_name, attr_value = attr.split(':', 1)
        attr_name = attr_name.strip()
        attr_value = attr_value.strip()

        # Support multiple values (comma separated)
        values = [v.strip() for v in attr_value.split(',') if v.strip()]

        # 1. Find attribute (vendor-specific first, then global)
        category = product_obj.category
        attribute_qs = ProductAttribute.objects.filter(
            name__iexact=attr_name,
            category=category,
        ).filter(
            models.Q(vendor=vendor) | models.Q(vendor__isnull=True)
        )

        if attribute_qs.exists():
            attribute_obj = attribute_qs.first()
        else:
            # Create vendor-specific attribute
            attribute_obj = ProductAttribute.objects.create(
                name=attr_name,
                category=category,
                vendor=vendor,
                is_active=True,
            )

        # 2. Save ProductAttributeValue(s)
        for value in values:
            ProductAttributeValue.objects.update_or_create(
                product=product_obj,
                attribute=attribute_obj,
                defaults={'value': value}
            )




def safe_decimal(val, default=Decimal(0), field_name=None):
    try:
        print("typeof val", field_name, type(val))
        val = str(val).strip()
        return Decimal(val) if val not in (None, '', '-') else default
    except Exception:
        return default
    
# def safe_decimal(value, field_name=None, fallback=0):
#     try:
#         return Decimal(str(value))
#     except (InvalidOperation, TypeError, ValueError):
#         return Decimal(str(fallback))



def normalize_variant_name(name):
    return name.strip().lower().replace(' ', '').replace('_', '')


@transaction.atomic
def save_product_variants(product_obj, variant_str):
    """
    Parses and saves variant attributes, values, and groups for a product.
    If a group with the same set of variant values exists for the product, it is updated.
    Handles stock, sku (barcode), and price.
    """
    if not variant_str:
        return

    # Prepare list of all valid variant keys from DB
    variant_attr_objs = {normalize_variant_name(v.name): v for v in VariantAttribute.objects.filter(is_active=True)}
    valid_variant_keys = set(variant_attr_objs.keys())
    stock_keys = {'stock', 'quantity'}
    barcode_keys = {'barcode'}
    price_keys = {'price'}

    # Split into variant groups by ;
    variant_groups = [g.strip() for g in variant_str.split(';') if g.strip()]
    for group_str in variant_groups:
        attrs = []  # List of VariantAttributeValue
        stock_val = None
        sku_val = None
        price_val = None

        # Split by comma to get "key:value"
        pairs = [p.strip() for p in group_str.split(',') if p.strip()]
        for pair in pairs:
            if ':' not in pair:
                continue  # Malformed, skip
            key, value = pair.split(':', 1)
            key = key.strip()
            value = value.strip()
            key_norm = normalize_variant_name(key)

            if key_norm in valid_variant_keys:
                # Find or create VariantAttributeValue
                attr_obj = variant_attr_objs[key_norm]
                vav, _ = VariantAttributeValue.objects.get_or_create(
                    attribute=attr_obj,
                    product=product_obj,
                    value=value
                )
                attrs.append(vav)
            elif key_norm in stock_keys:
                stock_val = value
            elif key_norm in barcode_keys:
                sku_val = value
            elif key_norm in price_keys:
                price_val = value
            else:
                continue  # Ignore unknown fields

        # Create or update ProductVariantGroup for this group
        if attrs:  # Only if there's at least one variant attribute
            # Try to find an existing group with exactly these attributes
            existing_group = None
            attr_ids = set(vav.id for vav in attrs)
            for group in ProductVariantGroup.objects.filter(product=product_obj):
                group_attr_ids = set(group.attribute.values_list('id', flat=True))
                if group_attr_ids == attr_ids and len(group_attr_ids) == len(attr_ids):
                    existing_group = group
                    break

            if existing_group:
                # Update stock, sku, price
                existing_group.stock = stock_val if stock_val is not None else existing_group.stock
                existing_group.sku = sku_val if sku_val else existing_group.sku
                existing_group.price = price_val if price_val is not None else existing_group.price
                existing_group.save()
            else:
                # Create new
                group = ProductVariantGroup.objects.create(
                    product=product_obj,
                    stock=stock_val if stock_val is not None else 0,
                    sku=sku_val if sku_val else None,
                    price=price_val if price_val is not None else None,
                )
                group.attribute.set(attrs)
                group.save()