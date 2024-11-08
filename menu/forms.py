from django import forms

from accounts.validators import allow_only_images_validator
from .models import Category,FoodItem,Product


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['category_name', 'description']


class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['category_name', 'description', 'parent']

    def __init__(self, *args, vendor=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter the parent field to show only main categories for this vendor
        if vendor:
            self.fields['parent'].queryset = Category.objects.filter(vendor=vendor, parent=None)
        
        # Set the label for the parent field and make it required
        self.fields['parent'].label = "Main Category"
        # self.fields['parent'].required = True

        # Disable the parent field if it has an initial value
        if 'parent' in self.initial:
            self.fields['parent'].widget.attrs['readonly'] = True
            self.fields['parent'].widget.attrs['disabled'] = True  # disable the field to make it non-editable

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product

        fields = ['product_name', 'description', 'full_specification', 'regular_price', 'sale_price', 'image', 'stock', 'is_available', 'category', 'subcategory', 'is_popular', 'is_active']

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        
        # Only show main categories (parent categories without any parent)
        self.fields['category'].queryset = Category.objects.filter(parent__isnull=True)

        # If a category is selected, filter the subcategories
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = Category.objects.filter(parent_id=category_id)
            except (ValueError, TypeError):
                pass  # Handle invalid category ID
        else:
            self.fields['subcategory'].queryset = Category.objects.none()

class EditProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'product_name', 'category', 'subcategory', 'description','full_specification',
            'full_specification', 'regular_price', 'sale_price', 'image',
            'stock', 'is_available', 'is_popular', 'is_active'
        ]

    def __init__(self, *args, **kwargs):
        super(EditProductForm, self).__init__(*args, **kwargs)

        # Only show main categories (categories without a parent)
        self.fields['category'].queryset = Category.objects.filter(parent__isnull=True)

        # If editing an existing product, set subcategory choices based on selected category
        if 'category' in self.data:
            # When the form is submitted, filter subcategories based on selected category
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = Category.objects.filter(parent_id=category_id)
            except (ValueError, TypeError):
                self.fields['subcategory'].queryset = Category.objects.none()  # Empty queryset if error occurs
        elif self.instance.pk and self.instance.category:
            # When the form is loaded initially, filter subcategories based on existing category
            self.fields['subcategory'].queryset = Category.objects.filter(parent_id=self.instance.category.id)
        else:
            # Set subcategory choices to none initially
            self.fields['subcategory'].queryset = Category.objects.none()

class FoodItemForm(forms.ModelForm):
    image = forms.FileField(widget=forms.FileInput(attrs={'class': 'btn btn-info w-100'}), validators=[allow_only_images_validator])
    class Meta:
        model = FoodItem
        fields = ['category', 'food_title', 'description', 'price', 'image', 'is_available']