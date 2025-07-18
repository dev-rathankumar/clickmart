from django.urls import path, include
from . import views
from accounts import views as AccountViews
from unified.autocomplete import ProductByCategoryAutocomplete,SubCategoryByCategoryAutocomplete

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
    path('product-variant/<int:product_id>/', views.product_variant, name='product_variant'),
    path('variant-value/add/<int:product_id>/', views.add_variant_value, name='add_variant_value'),
    path('variant-value/edit/<int:variant_id>/', views.edit_variant_value, name='edit_variant_value'),
    path('variant-value/delete/<int:variant_id>/', views.delete_variant_value, name='delete_variant_value'),
    path('variant-group/create/<int:product_id>/', views.create_variant_group, name='create_variant_group'),
    path('variant-group/edit/<int:pk>/', views.edit_variant_group, name='edit_variant_group'),
    path('variant-group/delete/<int:pk>/', views.delete_variant_group, name='delete_variant_group'),


    
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
    path('import-your-data/upload_csv/', views.upload_csv, name='upload_csv'),
    path('import-your-data/map_headers/', views.map_headers, name='map_headers'),
    path('import-your-data/process_mapped_data/', views.process_mapped_data, name='process_mapped_data'),
    path('import-your-data/validate_import_data/', views.process_mapped_data, name='validate_import_data'),
    path('import-your-data/set_image_to_mapped_data/', views.set_image_to_mapped_data, name='set_image_to_mapped_data'),
    path('import-your-data/process_mapped_data_with_images/', views.process_mapped_data_with_images, name='process_mapped_data_with_images'),
    path('update-image-url-in-session/', views.update_image_url_in_session, name='update_image_url_in_session'),
    path('import-your-data/save_to_database/', views.save_to_database, name='save_to_database'),
    path('product-by-category-autocomplete/',ProductByCategoryAutocomplete.as_view(),name='product-by-category-autocomplete'),
    path('subcategory-by-category-autocomplete/',SubCategoryByCategoryAutocomplete.as_view(),name='subcategory-by-category-autocomplete'),


]