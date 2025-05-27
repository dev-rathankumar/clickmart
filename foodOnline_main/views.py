from django.shortcuts import render
from django.http import HttpResponse

from vendor.models import AdBanner, Vendor
# from menu.models import Product
from unified.models import Product, Category
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D # ``D`` is a shortcut for ``Distance``
from django.contrib.gis.db.models.functions import Distance
from homepage.models import HomePageBanner, CategoryBanner
from collections import defaultdict


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
    categories_home = Category.objects.filter(parent=None, is_active=True)

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
    context = {
        'products':products,
        'vendors': vendors,
        'categories_home': categories_home,
        'banner_chunks': banner_chunks,
        'homepagebanners': homepagebanners,
        'grouped_banners_list': grouped_banners_list,
    }
    return render(request, 'home.html', context)