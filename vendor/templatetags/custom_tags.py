from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, '')


@register.filter
def get_error_for_row(errors, row_idx):
    """Find error object for a row index (0-based). Returns None if not found."""
    for e in errors:
        # e.row is 1-based, row_idx is 0-based, so add 1
        if e.get('row') == row_idx + 1:
            return e
    return None


@register.filter
def is_valid_field(value, info_type):
    """
    Returns True if the value for the key is valid according to the rules:
    - If the key is 'cost_price', it must be an integer.
    - Add more custom field validation as needed.
    """
    if value:
        try:
            type_map = {
                'decimal': int,
                'int': int,
                'str': str,
            }
            
            value_type = type_map.get(info_type, str)
            coverted = value_type(value)
            return type(coverted) == value_type
        except (ValueError, TypeError):
            return False
    # Add other field-specific validations here if needed
    return True  # Default case: valid



@register.filter
def display_variants(variant_string):
    if not variant_string:
        return ""
    groups = [v.strip() for v in variant_string.split(';') if v.strip()]
    attr_map = {}
    for group in groups:
        pairs = [p.strip() for p in group.split(',') if p.strip()]
        for pair in pairs:
            if ':' in pair:
                key, value = pair.split(':', 1)
                key = key.strip()
                value = value.strip()
                attr_map.setdefault(key, []).append(value)
    output = []
    for key, values in attr_map.items():
        # JOIN VALUES WITH COMMA AND SPACE
        clean_values = ', '.join(values)
        output.append(f"{key}: {clean_values}")
    # JOIN GROUPS WITH <br>
    return "<br>".join(output)