from django import forms
from .models import User, UserProfile,DeliveryAddress
from .validators import allow_only_images_validator


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())
    phone_number = forms.CharField(required=True)
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password','phone_number']

    def clean(self):
        cleaned_data = super(UserForm, self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError(
                "Password does not match!"
            )


class UserProfileForm(forms.ModelForm):
    address = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Start typing...', 'required': 'required'}))
    profile_picture = forms.FileField(widget=forms.FileInput(attrs={'class': 'btn btn-info vendor-image-up-btn'}), validators=[allow_only_images_validator],required=False)
    cover_photo = forms.FileField(widget=forms.FileInput(attrs={'class': 'btn btn-info vendor-image-up-btn'}), validators=[allow_only_images_validator],required=False)
    
    # latitude = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    # longitude = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'cover_photo', 'address', 'country', 'state', 'city', 'pin_code', 'latitude', 'longitude']

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field == 'latitude' or field == 'longitude':
                self.fields[field].widget.attrs['readonly'] = 'readonly'


class UserInfoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number']



class DeliveryAddressForm(forms.ModelForm):
    class Meta:
        model = DeliveryAddress
        fields = [
            'full_name', 'phone_number', 'apartment_address',
            'state', 'city', 'postal_code', 'street_address',
            'country', 'is_primary'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'First Last'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Please enter your phone number'}),
            'apartment_address': forms.TextInput(attrs={'placeholder': 'E.g. beside train station (optional)'}),
            'state': forms.TextInput(attrs={'placeholder': 'Please enter your province / region'}),
            'city': forms.TextInput(attrs={'placeholder': 'Please enter your city'}),
            'postal_code': forms.TextInput(attrs={'placeholder': 'Please enter your postal code'}),
            'street_address': forms.TextInput(attrs={'placeholder': 'Please enter your address'}),
            'country': forms.TextInput(attrs={'placeholder': 'Please enter your country'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
