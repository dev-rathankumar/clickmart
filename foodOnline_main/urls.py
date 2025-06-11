"""foodOnline_main URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from marketplace import views as MarketplaceViews
from django.contrib.auth import views as auth_views
from inventory import views as inventory_views


urlpatterns = [
    path("ckeditor5/", include('django_ckeditor_5.urls')),
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('', include('accounts.urls')),

    path('marketplace/', include('marketplace.urls')),

    # CART
    path('cart/', MarketplaceViews.cart, name='cart'),
    # SEARCH
    path('search/', MarketplaceViews.search, name='search'),

    # CHECKOUT
    path('checkout/', MarketplaceViews.checkout, name='checkout'),

    # ORDERS
    path('orders/', include('orders.urls')),

    # POS URL ENDPOINTS
    path('pos/', include('pos.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "Flickbasket Admin"