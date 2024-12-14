from django import forms

from accounts.validators import allow_only_images_validator
from .models import FoodItem
from unified.models import Category, Product, ProductGallery
from django.forms import modelformset_factory


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['category_name', 'description','category_image']


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
            self.fields['parent'].widget = forms.HiddenInput()
from django.core.exceptions import ValidationError
from PIL import Image

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'product_name', 'product_desc', 'full_specification', 'hsn_number','cost_price', 'regular_price',
            'sales_price', 'image', 'category',
            'subcategory', 'barcode', 'qty', 'tax_category'
        ]

    def __init__(self, *args, **kwargs):
        
        vendor_id = kwargs.pop('vendor_id', None)
        super(ProductForm, self).__init__(*args, **kwargs)
        
        # Only show main categories (parent categories without any parent)
        self.fields['category'].queryset = Category.objects.filter(parent__isnull=True, vendor_id=vendor_id)

        # If a category is selected, filter the subcategories
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = Category.objects.filter(parent_id=category_id)
            except (ValueError, TypeError):
                pass  # Handle invalid category ID
        else:
            self.fields['subcategory'].queryset = Category.objects.none()

    # def clean_image(self):
    #     image = self.cleaned_data.get('image')
    #     if image:
    #         img = Image.open(image)
    #         if img.width != 480 or img.height != 480:
    #             raise ValidationError("Image must be 480x480 pixels.")
    #     return image
    
class EditProductForm(forms.ModelForm):
    class Meta:
        model = Product 
        fields = [
            'product_name', 'product_desc', 'full_specification', 'hsn_number', 'cost_price', 'regular_price',
            'sales_price', 'image', 'is_available', 'category',
            'subcategory', 'barcode', 'qty', 'tax_category'
        ]

    def __init__(self, *args, **kwargs):
        vendor_id = kwargs.pop('vendor_id', None)
        super(EditProductForm, self).__init__(*args, **kwargs)

        # Only show main categories (categories without a parent)
        self.fields['category'].queryset = Category.objects.filter(parent__isnull=True, vendor_id=vendor_id)


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


class ProductGalleryForm(forms.ModelForm):
    class Meta:
        model = ProductGallery
        fields = ['image']
    image = forms.ImageField(required=False)

ProductGalleryFormSet = modelformset_factory(ProductGallery, form=ProductGalleryForm, extra=3, max_num=3)