from dal import autocomplete
from .models import Product, Category

class ProductByCategoryAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Product.objects.all()
        category_id = self.forwarded.get('category_id', None)
        if category_id:
            qs = qs.filter(category_id=category_id)
        if self.q:
            qs = qs.filter(product_name__icontains=self.q)
        return qs