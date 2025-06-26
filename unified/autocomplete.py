from dal import autocomplete
from .models import Product, CategoryBrowseSection,Category
import json

class ProductByCategoryAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        print("GET:", self.request.GET)
        qs = Product.objects.all()

        # Try to get category_id from forwarded data
        category_id = self.forwarded.get('category', None)

        # Fallback: get section/object_id from GET param
        if not category_id:
            forward_data = self.request.GET.get('forward')
            section_id = None

            if forward_data:
                try:
                    data = json.loads(forward_data)
                    section_id = data.get('section')
                    print("Parsed section ID:", section_id)
                except json.JSONDecodeError:
                    print("Could not decode forward data:", forward_data)

            if section_id:
                try:
                    section = CategoryBrowseSection.objects.select_related('browse_page__category').get(pk=section_id)
                    category_id = section.browse_page.category_id
                except CategoryBrowseSection.DoesNotExist:
                    print("Section not found")

        if category_id:
            qs = qs.filter(category_id=category_id)

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs



# This is for the subcatgory
class SubCategoryByCategoryAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        print("GET:", self.request.GET)
        qs = Category.objects.filter(parent__isnull=False)
        print("qs data:", qs)

        # Try to get category_id from forwarded data
        category_id = self.forwarded.get('category', None)

        # Fallback: get section/object_id from GET param
        if not category_id:
            forward_data = self.request.GET.get('forward')
            section_id = None

            if forward_data:
                try:
                    data = json.loads(forward_data)
                    section_id = data.get('section')
                    print("Parsed section ID:", section_id)
                except json.JSONDecodeError:
                    print("Could not decode forward data:", forward_data)

            if section_id:
                try:
                    section = CategoryBrowseSection.objects.select_related('browse_page__category').get(pk=section_id)
                    category_id = section.browse_page.category_id
                except CategoryBrowseSection.DoesNotExist:
                    print("Section not found")

        if category_id:
            print("Filtering by category_id:", category_id)
            qs = qs.filter(parent_id=category_id)
            print("Filtered qs data:", qs)

        if self.q:
            qs = qs.filter(name__icontains=self.q, parent__isnull=False)

        return qs
