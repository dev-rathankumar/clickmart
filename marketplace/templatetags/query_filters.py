from django import template
from urllib.parse import urlencode

register = template.Library()

@register.filter
def remove_query_param(request, param):
    if hasattr(request, 'GET'):
        query = request.GET.copy()
        if param in query:
            query.pop(param)
        return '?' + urlencode(query, doseq=True) if query else request.path
    return request  # If a string or other object is passed, return it unchanged