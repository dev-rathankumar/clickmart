from django.urls import path
from . import views

urlpatterns = [
    path('', views.marketplace, name='marketplace'),
    path('categories/', views.categories, name='categories'),
    
    # All Products
    path('products/', views.All_products, name='all_products'),
    path('products/category/<int:category_id>/', views.All_products, name='filter_by_category'),
    path('products/subcategory/<int:subcategory_id>/', views.All_products, name='filter_by_subcategory'),
    
    path('product/<slug:vendor_slug>/<slug:product_slug>/', views.view_Product, name='view_product'),

    path('<slug:vendor_slug>/', views.vendor_detail, name='vendor_detail'),
    path('<slug:vendor_slug>/category/<int:category_id>/', views.vendor_detail, name='vendor_detail_filter_by_category'),
    path('<slug:vendor_slug>/subcategory/<int:subcategory_id>/', views.vendor_detail, name='vendor_detail_filter_by_subcategory'),

    path('add_product_cart/<int:product_id>/',views.add_product_to_cart, name="add_product_to_cart"),
    # ADD TO CART
    path('add_to_cart/<int:food_id>/', views.add_to_cart, name='add_to_cart'),
    # DECREASE CART
    path('decrease_cart/<int:food_id>/', views.decrease_cart, name='decrease_cart'),
    # DELETE CART ITEM
    path('delete_cart/<int:cart_id>/', views.delete_cart, name='delete_cart'),

    path('browse/<slug:category_slug>/', views.browse, name='browse'),

]