from django import forms

from accounts.validators import allow_only_images_validator
from .models import FoodItem
from unified.models import Category, Product, ProductGallery
from django.forms import modelformset_factory
from vendor.models import Vendor

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['category_name', 'description','category_image']


class SubCategoryForm(forms.ModelForm):
    category_image = forms.FileField(widget=forms.FileInput(attrs={'class': 'btn btn-info vendor-image-up-btn'}), validators=[allow_only_images_validator],required=False)

    class Meta:
        model = Category
        fields = ['category_name', 'description', 'parent','category_image']

    def __init__(self, *args, vendor=None, **kwargs):
        super().__init__(*args, **kwargs)
        print("vendor line 22", vendor)
        # Filter the parent field to show only main categories for this vendor
        if vendor:
            self.fields['parent'].queryset = Category.objects.filter(store_type=vendor.store_type, parent=None)
        
        # Set the label for the parent field and make it required
        self.fields['parent'].label = "Main Category"
        # self.fields['parent'].required = True

        # Disable the parent field if it has an initial value
        if 'parent' in self.initial:
            self.fields['parent'].widget = forms.HiddenInput()


from django.core.exceptions import ValidationError
from PIL import Image
from accounts.validators import allow_only_images_validator

class ProductForm(forms.ModelForm):
    image = forms.FileField(widget=forms.FileInput(attrs={'class': 'btn btn-sm vendor-image-up-btn'}), validators=[allow_only_images_validator])

    class Meta:
        model = Product
        fields = [
            'product_name', 'product_desc', 'full_specification', 'hsn_number','model_number','cost_price', 'regular_price',
            'sales_price', 'image', 'category',
            'subcategory', 'barcode','unit_type', 'qty', 'tax_category'
        ]

    def __init__(self, *args, **kwargs):
        
        vendor_id = kwargs.pop('vendor_id', None)
        super(ProductForm, self).__init__(*args, **kwargs)
        if vendor_id: 
            vendor = Vendor.objects.get(id=vendor_id)
        
        # Only show main categories (parent categories without any parent)
        self.fields['category'].queryset = Category.objects.filter(parent__isnull=True, store_type=vendor.store_type)

        # If a category is selected, filter the subcategories
        self.fields['subcategory'].required = False
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = Category.objects.filter(parent_id=category_id,vendor_subcategory_reference_id=vendor_id)
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
    image = forms.FileField(widget=forms.FileInput(attrs={'class': 'btn btn-sm vendor-image-up-btn'}), validators=[allow_only_images_validator])

    class Meta:
        model = Product 
        fields = [
            'product_name', 'product_desc', 'full_specification', 'hsn_number', 'model_number','cost_price', 'regular_price',
            'sales_price', 'image', 'is_available', 'category',
            'subcategory', 'barcode','unit_type', 'qty', 'tax_category'
        ]

    def __init__(self, *args, **kwargs):
        vendor_id = kwargs.pop('vendor_id', None)
        super(EditProductForm, self).__init__(*args, **kwargs)
        if vendor_id: 
                vendor = Vendor.objects.get(id=vendor_id)
        # Only show main categories (categories without a parent)
        self.fields['category'].queryset = Category.objects.filter(parent__isnull=True,store_type=vendor.store_type)

        self.fields['subcategory'].required = True
        # If editing an existing product, set subcategory choices based on selected category
        if 'category' in self.data:
            # When the form is submitted, filter subcategories based on selected category
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = Category.objects.filter(parent_id=category_id, vendor_subcategory_reference_id=vendor.id)
            except (ValueError, TypeError):
                self.fields['subcategory'].queryset = Category.objects.none()  # Empty queryset if error occurs
        elif self.instance.pk and self.instance.category:
            # When the form is loaded initially, filter subcategories based on existing category
            self.fields['subcategory'].queryset = Category.objects.filter(parent_id=self.instance.category.id, vendor_subcategory_reference_id=vendor.id)
        else:
            # Set subcategory choices to none initially
            self.fields['subcategory'].queryset = Category.objects.none()


class FoodItemForm(forms.ModelForm):
    image = forms.FileField(widget=forms.FileInput(attrs={'class': 'btn btn-info w-100'}), validators=[allow_only_images_validator])
    class Meta:
        model = FoodItem
        fields = ['category', 'food_title', 'description', 'price', 'image', 'is_available']


class ProductGalleryForm(forms.ModelForm):
    image = forms.FileField(widget=forms.FileInput(attrs={'class': 'btn btn-sm vendor-image-up-btn'}), validators=[allow_only_images_validator])

    class Meta:
        model = ProductGallery
        fields = ['id','image']
    image = forms.ImageField(required=False)

ProductGalleryFormSet = modelformset_factory(ProductGallery, form=ProductGalleryForm, extra=3, max_num=3)