from django import forms
from .models import User, UserProfile,DeliveryAddress
from .validators import allow_only_images_validator
from django.core.validators import MaxLengthValidator

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())
    phone_number = forms.CharField(required=True,max_length=12,validators=[MaxLengthValidator(12)],)
    first_name = forms.CharField(max_length=50,validators=[MaxLengthValidator(50)],)
    last_name = forms.CharField(max_length=50,validators=[MaxLengthValidator(50)],)
    email = forms.EmailField(max_length=100,validators=[MaxLengthValidator(100)],)
    # If you want to allow users to set username via this form, add:
    # username = forms.CharField(max_length=50, validators=[MaxLengthValidator(50)])

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'phone_number']

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs.update({
            'placeholder': 'Enter first name',
            'autocomplete': 'off',
            'maxlength': 50
        })
        self.fields['last_name'].widget.attrs.update({
            'placeholder': 'Enter last name',
            'autocomplete': 'off',
            'maxlength': 50
        })
        self.fields['email'].widget.attrs.update({
            'placeholder': 'Enter email',
            'autocomplete': 'off',
            'maxlength': 100
        })
        self.fields['password'].widget.attrs.update({
            'placeholder': 'Create password',
            'autocomplete': 'new-password'
        })
        self.fields['confirm_password'].widget.attrs.update({
            'placeholder': 'Confirm password',
            'autocomplete': 'new-password'
        })
        self.fields['phone_number'].widget.attrs.update({
            'placeholder': 'Enter phone number',
            'autocomplete': 'off',
            'maxlength': 12
        })

    def clean(self):
        cleaned_data = super(UserForm, self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError("Password does not match!")
        return cleaned_data

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
