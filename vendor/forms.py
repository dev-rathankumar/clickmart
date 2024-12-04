from django import forms
from .models import Vendor, OpeningHour
from accounts.validators import allow_only_images_validator


class VendorForm(forms.ModelForm):
    vendor_license = forms.FileField(widget=forms.FileInput(attrs={'class': 'btn btn-info'}), validators=[allow_only_images_validator])
    class Meta:
        model = Vendor
        fields = ['vendor_name', 'vendor_license', 'gst_number', 'fssai_number']


class OpeningHourForm(forms.ModelForm):
    class Meta:
        model = OpeningHour
        fields = ['day', 'from_hour', 'to_hour', 'is_closed']


class CategoryImportForm(forms.Form):
    category_file = forms.FileField()

class ProductImportForm(forms.Form):
    products_file = forms.FileField()