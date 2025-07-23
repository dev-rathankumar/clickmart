from django import template

register = template.Library()

@register.filter
def extract_variant(product):
    try:
        title = str(product)
        # Split using the LAST " - " in the string
        if ' - ' in title:
            return title.rsplit(' - ', 1)[-1]
        return title
    except Exception:
        return ''
