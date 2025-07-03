from django.shortcuts import render
from django.http import HttpResponse

from mobile.utils import get_current_event
from homepage.product_collections import get_products_for_collection
from vendor.models import AdBanner, Vendor
# from menu.models import Product
from unified.models import Product, Category
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D # ``D`` is a shortcut for ``Distance``
from django.contrib.gis.db.models.functions import Distance
from homepage.models import HomePageBanner, CategoryBanner
from collections import defaultdict
from marketplace.models import Cart
from homepage.models import ProductCollection


def get_or_set_current_location(request):
    if 'lat' in request.session:
        lat = request.session['lat']
        lng = request.session['lng']
        print("latitute",lat)
        print("longitute",lng)
        return lng, lat
    elif 'lat' in request.GET:
        lat = request.GET.get('lat')
        lng = request.GET.get('lng')
        request.session['lat'] = lat
        request.session['lng'] = lng
        print("latitute",lat)
        print("longitute",lng)
        return lng, lat
    else:
        return None


def home(request):
    if get_or_set_current_location(request) is not None:

        pnt = GEOSGeometry('POINT(%s %s)' % (get_or_set_current_location(request)))

        vendors = Vendor.objects.filter(user_profile__location__distance_lte=(pnt, D(km=1000))).annotate(distance=Distance("user_profile__location", pnt)).order_by("distance")

        for v in vendors:
            v.kms = round(v.distance.km, 1)
    else:
        vendors = Vendor.objects.filter(is_approved=True, user__is_active=True)[:8]

    products = Product.objects.filter(is_active=True)[:10]

    # Product Collections
    collections = ProductCollection.objects.filter(active=True)
    collection_data = []
    for collection in collections:
        products = get_products_for_collection(collection.logic)
        collection_data.append({
            'name': collection.name,
            'slug': collection.slug,
            'products': products,
        })
    categories_home = Category.objects.filter(parent=None, is_active=True)
    user_cart = Cart.objects.filter(user=request.user) if request.user.is_authenticated else []
    cart_vendors = set(item.product.vendor_id for item in user_cart)

    for product in products:
        # True if cart is not empty and this product's vendor is NOT in the cart's vendors
        product.is_different_vendor_for_cart = bool(cart_vendors) and (product.vendor_id not in cart_vendors)

    banners = AdBanner.objects.all()
    # Split the banners into chunks of 3
    banner_chunks = [banners[i:i+3] for i in range(0, len(banners), 3)]
    
    homepagebanners = HomePageBanner.objects.filter(is_active=True)
    category_banners = CategoryBanner.objects.select_related('category').filter(is_active=True, category__isnull=False)
    grouped_banners = defaultdict(list)
    for banner in category_banners:
        if banner.category.parent is None:
            grouped_banners[banner.category].append(banner)
    def chunked(iterable, size):
        for i in range(0, len(iterable), size):
            yield iterable[i:i+size]
    grouped_banners_list = [
        (category, list(chunked(banners, 3)))
        for category, banners in grouped_banners.items()
    ]
    if request.user.is_authenticated:
        cart_items = []
        for cart_obj in Cart.objects.filter(user=request.user).order_by('created_at'):
            cart_items.append({
                'product': cart_obj.product,
                'quantity': cart_obj.quantity,
                'cart_id': cart_obj.id,  # DB cart uses Cart PK
            })
    else:
        cart = request.session.get('cart', {})
        product_ids = list(cart.keys())
        cart_products  = Product.objects.filter(id__in=product_ids)
        cart_items = []
        for product in cart_products :
            print("product_id ===>", product.id)
            quantity = cart.get(str(product.id))
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'cart_id': product.id,  # session cart uses product id
            })
    cart_product_ids = set(item['product'].id for item in cart_items)

    # Mobile homepage banners
    current_event = get_current_event()
    ads = current_event.ads.all() if current_event else []

    print("this is bannar", banners)

    context = {
        'products':products,
        'vendors': vendors,
        'categories_home': categories_home,
        'banner_chunks': banner_chunks,
        'all_banners': banners,
        'homepagebanners': homepagebanners,
        'grouped_banners_list': grouped_banners_list,
        'collections': collection_data, 
        'cart_items': cart_items,
        'cart_product_ids': cart_product_ids,
        'current_event': current_event,
        'ads': ads,
    }
    return render(request, 'home.html', context)