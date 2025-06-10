from django import forms
from .models import Vendor, OpeningHour
from accounts.validators import allow_only_images_validator


class VendorForm(forms.ModelForm):
    vendor_license = forms.FileField(widget=forms.FileInput(attrs={'class': 'btn btn-info vendor-image-up-btn'}), validators=[allow_only_images_validator])

    class Meta:
        model = Vendor
        fields = ['vendor_name', 'store_type', 'vendor_license', 'gst_number', 'fssai_number', 'delivery_radius']

    def __init__(self, *args, **kwargs):
        super(VendorForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Disable the store_type field if updating an existing vendor
            self.fields['store_type'].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        if self.instance and self.instance.pk:
            # Ensure store_type can't be changed via form manipulation
            cleaned_data['store_type'] = self.instance.store_type
        return cleaned_data


class OpeningHourForm(forms.ModelForm):
    class Meta:
        model = OpeningHour
        fields = ['day', 'from_hour', 'to_hour', 'is_closed']
        widgets = {
            'day': forms.Select(attrs={'class': 'custom-day-class'}),
            'from_hour': forms.Select(attrs={'class': 'custom-from-hour-class'}),
            'to_hour': forms.Select(attrs={'class': 'custom-to-hour-class'}),
        }


class CategoryImportForm(forms.Form):
    category_file = forms.FileField()

class ProductImportForm(forms.Form):
    products_file = forms.FileField()