from urllib.parse import uses_relative
from accounts.models import UserProfile
from vendor.models import Vendor
from django.conf import settings
from vendor.models import StoreType

def get_vendor(request):
    try:
        vendor = Vendor.objects.get(user=request.user)
    except:
        vendor = None
    return dict(vendor=vendor)


def get_user_profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except:
        user_profile = None
    return dict(user_profile=user_profile)



def get_google_api(request):
    return {'GOOGLE_API_KEY': settings.GOOGLE_API_KEY}


def get_paypal_client_id(request):
    return {'PAYPAL_CLIENT_ID': settings.PAYPAL_CLIENT_ID}


def get_store_types(request):
    store_types_footer = StoreType.objects.order_by('-id')[:6]
    print("Store types in context:", store_types_footer)
    return {'store_types_footer': store_types_footer}