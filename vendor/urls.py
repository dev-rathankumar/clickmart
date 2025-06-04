from django.urls import path, include
from . import views
from accounts import views as AccountViews


urlpatterns = [
    path('', AccountViews.vendorDashboard, name='vendor'),
    path('profile/', views.vprofile, name='vprofile'),

    # Categories 
    path('manage-categories/categories-builder/', views.category_builder, name='category_builder'),
    path('manage-categories/category/<int:pk>/', views.fooditems_by_category, name='fooditems_by_category'),
    # path('manage-categories/category/edit/<int:pk>/', views.edit_category, name='edit_category'),
    # path('manage-categories/category/delete/<int:pk>/', views.delete_category, name='delete_category'),

    # SubCategories
    path('manage-categories/add-sub-category/<int:category_id>/', views.add_sub_category, name='add_sub_category'),
    path('manage-categories/subcategories-builder/<int:pk>/', views.subcategory_builder, name='subcategory_builder'),
    path('manage-categories/edit-subcategory/<int:category_id>/<int:pk>/', views.edit_subcategory, name='edit_subcategory'),
    path('manage-categories/subcategory/delete/<int:pk>/', views.delete_subcategory, name='delete_subcategory'),
    path('get-subcategories/<int:category_id>/', views.get_subcategories, name='get_subcategories'),
    # path('manage-categories/category/add/', views.add_category, name='add_category'),

    #Product 
    path('manage-products/products/', views.product_list_view, name='vendor_products_list'),
    path('manage-products/products/import/', views.import_products, name='import_products'),
    path('manage-products/add-product/', views.add_product, name='add_product'),
    path('manage-products/edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('manage-products/product-delete/<int:product_id>/', views.delete_product, name='delete_product'),
    
    # Category CRUD

    # FoodItem CRUD
    path('menu-builder/food/add/', views.add_food, name='add_food'),
    path('menu-builder/food/edit/<int:pk>/', views.edit_food, name='edit_food'),
    path('menu-builder/food/delete/<int:pk>/', views.delete_food, name='delete_food'),

    # Opening Hour CRUD
    path('opening-hours/', views.opening_hours, name='opening_hours'),
    path('opening-hours/add/', views.add_opening_hours, name='add_opening_hours'),
    path('opening-hours/remove/<int:pk>/', views.remove_opening_hours, name='remove_opening_hours'),

    path('order_detail/<int:order_number>/', views.order_detail, name='vendor_order_detail'),
    path('my_orders/', views.my_orders, name='vendor_my_orders'),

    path('order-status/', views.order_status, name='order_status'),

    path('media-library/', views.media_library, name='media_library'),

    path('media-library/upload/', views.FileUploadView.as_view(), name='media_upload'),
    path('import-your-data/source/', views.import_your_data, name='import_your_data'),
    path('import-your-data/connect/', views.connect_erp, name='connect_erp'),


]