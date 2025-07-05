from django.conf import settings
from django.core.mail import EmailMessage
from unicodedata import category
from urllib import response
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.db import IntegrityError
import requests
import django.contrib as massage_helper
from menu.forms import CategoryForm, FoodItemForm, ProductGalleryForm, SubCategoryForm, ProductForm,EditProductForm
from orders.models import Order, OrderedFood
# from menu.models import Product,ProductGallery
from unified.models import Product,ProductGallery
import vendor
from vendor.constants import CSV_FIELD_MAPPINGS
from .forms import VendorForm, OpeningHourForm, CategoryImportForm, ProductImportForm, CSVUploadForm
from accounts.forms import UserInfoForm, UserProfileForm

from accounts.models import UserProfile
from .models import OpeningHour, StoreType, Vendor
from django.contrib import messages

from django.contrib.auth.decorators import login_required, user_passes_test
from accounts.views import check_role_vendor
from menu.models import Category, FoodItem
from django.template.defaultfilters import slugify
from django.db.models import Count, Q
import csv
from inventory.models import tax as Tax

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from unified.models import MediaUpload, ProductCloneTable

from django.forms import modelformset_factory

from django.core.files.base import ContentFile
from urllib.request import urlretrieve
from io import BytesIO
from accounts.utils import send_notification
import io

import simplejson as json

from django.core.paginator import Paginator

import csv, io, os
from urllib.parse import urlparse
from decimal import Decimal, InvalidOperation
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponse
from django.db import transaction
from unified.models import Product, Category
from inventory.models import tax as TaxCategory
from inventory.models import deposit as DepositCategory
from vendor.models import Vendor
from django.template.defaultfilters import slugify
import decimal


def get_vendor(request):
    vendor = Vendor.objects.get(user=request.user)
    return vendor


@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def vprofile(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    vendor = get_object_or_404(Vendor, user=request.user)

    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        vendor_form = VendorForm(request.POST, request.FILES, instance=vendor)
        user_form = UserInfoForm(request.POST, instance=request.user)
        if profile_form.is_valid() and vendor_form.is_valid() and user_form.is_valid():
            profile_form.save()
            vendor_form.save()
            user_form.save()
            messages.success(request, 'Settings updated.')
            return redirect('vprofile')
        else:
            print(profile_form.errors)
            print(vendor_form.errors)
            print(user_form.errors)
    else:
        profile_form = UserProfileForm(instance = profile)
        vendor_form = VendorForm(instance=vendor)
        user_form = UserInfoForm(instance=request.user)

    context = {
        'profile_form': profile_form,
        'vendor_form': vendor_form,
        'profile': profile,
        'vendor': vendor,
        'user_form': user_form,
    }
    return render(request, 'vendor/vprofile.html', context)


#*  ================ Category section =============== 
@login_required(login_url='login')
@user_passes_test(check_role_vendor)

def category_builder(request):
    vendor = get_vendor(request)
    store_type = vendor.store_type
    if vendor.store_type is None:
        messages.error(request, "Vendor doesn't have a store type. Please contact the admin.")
        return redirect("vendor")
    
    categories = Category.objects.filter(
        store_type=vendor.store_type, 
        parent__isnull=True
    ).annotate(
        subcategory_count=Count(
            'subcategories',
            filter=Q(
                subcategories__vendor_subcategory_reference_id=vendor.id
            )
        )
    ).order_by('created_at')
    
    context = {
        'categories': categories,
        'store_type': store_type,
    }
    return render(request, 'vendor/menu_builder.html', context)

def import_categories(request):
    if request.method == 'POST' and request.FILES['category_file']:
        csv_file = request.FILES['category_file']
        # Only allow CSV file
        if not csv_file.name.endswith('.csv'):
            messages.error(request, f"Please upload a CSV file.")
            return redirect('import_categories')

        
        # Decode the file and read it
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        categories_to_create = []
        for row in reader:
            try:
                category_name = row['category_name']
                parent_category_name = row['parent_category']
                user = request.user
                vendor = Vendor.objects.get(user=user, is_approved=True)
                category_description = row['category_description']
                category_image_path = row['category_image']

                # Check if category already exists for the vendor
                existing_category = Category.objects.filter(
                    category_name=category_name,
                    vendor=vendor
                ).exists()
                if existing_category:
                    messages.error(request, f"Category '{category_name}' already exists. Please check your data. ")
                    return redirect('import_categories')
                
                main_content_file = None
                  
                if category_image_path: 
                    main_image_filename = category_image_path.split('/')[-1]
                    main_img_content = requests.get(category_image_path).content
                    main_content_file = ContentFile(main_img_content, name=main_image_filename)
                
                parent_category=None
                
                if parent_category_name:
                    try:
                        parent_category = Category.objects.get(category_name=parent_category_name, vendor=vendor)
                    except Category.DoesNotExist:
                        parent_category = Category.objects.create(
                            category_name=parent_category_name,
                            slug=slugify(parent_category_name),
                            category_image=main_content_file,
                            is_active=True,  # Assuming new categories are active by default
                            vendor=vendor,  # You can adjust this depending on your business logic
                        )
                        print(f"Parent category '{parent_category_name}' not found. This category will be treated as a top-level category.")
                
                # Handle Slug (generate if not present)
                slug = slugify(category_name)

                # Create category object
                category = Category(
                    category_name=category_name,
                    slug=slug,
                    description=category_description,
                    category_image=main_content_file,
                    is_active=True,  # Assuming new categories are active by default
                    parent=parent_category,  # Parent will be None if no parent category
                    vendor=vendor,
                )
                categories_to_create.append(category)
                
            except KeyError:
                messages.error(request, f"CSV format is incorrect. Missing required fields.")
                continue

            except Exception as e:
                messages.error(request, f"Error processing row: {e}")
                continue

            
        # Bulk insert the categories
        if categories_to_create:
            Category.objects.bulk_create(categories_to_create)        
        messages.success(request, "Categories imported successfully!")
        return redirect('import_categories')
    else:
        form = CategoryImportForm()
    return render(request, 'vendor/import_categories.html', {'form': form})


def import_products(request):
    if request.method == "POST" and request.FILES.get("products_file"):
        csv_file = request.FILES["products_file"]
        # Validate file type
        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Please upload a valid CSV file.")
            return redirect('import_products')
        
        # Decode and read the file
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        for row in reader:
            try:
                # Extract fields from CSV
                barcode = row['barcode']
                product_name = row['product_name'].strip()
                product_desc = row['product_desc'].strip()
                full_specification = row['full_specification'].strip()
                hsn_number = row['hsn_number']
                model_number = row['model_number']
                cost_price = row['purchase_price']
                regular_price = row['regular_price']
                sales_price = row['sales_price']
                image = row['image']
                gallery_image_1 = row['gallery_image_1']
                gallery_image_2 = row['gallery_image_2']
                gallery_image_3 = row['gallery_image_3']
                category_name = row['category'].strip()
                subcategory_name = row.get('subcategory', "").strip().replace(" ", "")
                tax_category_name = row['tax_category'].strip().replace(" ", "")
                tax_percentage = row['tax_percentage'].strip().replace(" ", "")
                unit_type= row['unit_type']
                qty = row['stock']

                user = request.user
                vendor = Vendor.objects.get(user=user, is_approved=True)

                # Check if product with the same barcode already exists
                if Product.objects.filter(barcode=barcode , vendor=vendor).exists():
                    print(f"Product with barcode '{barcode}' already exists. Skipping product '{product_name}'.")
                    messages.error(request, f"Error processing product '{row.get('product_name', 'Unknown')}': {e}")

                # Handle ForeignKey relationships
                print('category name==>', category_name)
                try:
                    category = Category.objects.get(category_name=category_name, store_type=vendor.store_type)
                except Category.DoesNotExist:
                    messages.error(request, f"The Category '{category_name}' does not exist. Please ensure the category name matches exactly.")
                    continue  # Skip this row
                subcategory = None
                print(subcategory_name)
                if subcategory_name:
                    slug = slugify(f"{subcategory_name}{category_name}{vendor.id}")
                    print(slug)
                    try:
                        subcategory = Category.objects.get(category_name=subcategory_name, vendor_subcategory_reference_id=vendor.id,slug=slug )
                        print(subcategory)
                    except Category.DoesNotExist:
                        # If subcategory doesn't exist, create a new one and link to the parent category
                        subcategory = Category.objects.create(
                            category_name=subcategory_name,
                            category_code=f"SUB-{subcategory_name.capitalize()}-{category.category_code}-{vendor.id}",
                            slug=slug,
                            parent=category,  # Setting the main category as parent
                            vendor_subcategory_reference_id=vendor.id,
                            description="",
                        )
                        subcategory.save()
                        print(f"Subcategory '{subcategory_name}' created under parent category '{category_name}'.")

                try:
                    tax_instance = Tax.objects.filter(tax_category=tax_category_name, tax_percentage=tax_percentage).first()
                    if not tax_instance:
                        tax_instance = Tax.objects.create(
                        tax_category=tax_category_name,
                        tax_percentage=tax_percentage,
                        tax_desc=''
                        )
                        tax_instance.save()
                        print(f"Tax category '{tax_category_name}' with {tax_percentage}% created.")
                except Tax.DoesNotExist:
                    messages.error(request, f"Tax category '{tax_category_name}' not found. Skipping product '{product_name}'.")
                    continue

                main_image_filename = image.split('/')[-1]
                main_img_content = requests.get(image).content
                main_content_file = ContentFile(main_img_content, name=main_image_filename)
                # Create product instance
                product = Product(
                    barcode=barcode,
                    vendor=vendor,
                    product_name=product_name,
                    slug=slugify(product_name),
                    product_desc=product_desc,
                    full_specification=full_specification,
                    hsn_number=hsn_number,
                    model_number=model_number,
                    cost_price=cost_price,
                    regular_price=regular_price,
                    sales_price=sales_price,
                    image=main_content_file,
                    category=category,
                    subcategory=subcategory,
                    qty=qty,
                    tax_category=tax_instance,
                    unit_type=unit_type,
                )
                product.save()

                # Save gallery images
                gallery_images = [gallery_image_1, gallery_image_2, gallery_image_3]
                for idx, gallery_image_url in enumerate(gallery_images):
                    if gallery_image_url:
                        try:
                            # Fetch the image content from the URL
                            image_filename = gallery_image_url.split('/')[-1]
                            img_content = requests.get(gallery_image_url).content
                            content_file = ContentFile(img_content, name=image_filename)

                            # Create ProductGallery instance
                            product_gallery = ProductGallery(
                                product=product,
                                image=content_file
                            )
                            product_gallery.save()  # Save the gallery image
                            messages.success(request, "Products imported successfully!")
                            print(f"Gallery image {idx + 1} for product '{product.product_name}' saved.")
                        except Exception as e:
                            print(f"Error saving gallery image {idx + 1} for product '{product.product_name}': {e}")
            except KeyError as e:
                messages.error(request, f"Missing field '{e}' in the CSV file. Please check your data.")
                continue
            except Exception as e:
                print(str(e))
                messages.error(request, f"Error processing product '{row.get('product_name', 'Unknown')}': {e}")
                continue
        return redirect('import_products')
    form = ProductImportForm()
    return render(request, 'vendor/import_products.html', {'form': form})



@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def fooditems_by_category(request, pk=None):
    vendor = get_vendor(request)
    category = get_object_or_404(Category, pk=pk)
    fooditems = FoodItem.objects.filter(vendor=vendor, category=category)
    context = {
        'fooditems': fooditems,
        'category': category,
    }
    return render(request, 'vendor/fooditems_by_category.html', context)


# @login_required(login_url='login')
# @user_passes_test(check_role_vendor)
# def add_category(request):
#     if request.method == 'POST':
#         form = CategoryForm(request.POST,request.FILES)
#         if form.is_valid():
#             category_name = form.cleaned_data['category_name']
#             category = form.save(commit=False)
#             category.vendor = get_vendor(request)
            
#             category.save() # here the category id will be generated
#             category.slug = slugify(category_name)+'-'+str(category.id) # chicken-15
#             category.save()
#             messages.success(request, 'Category added successfully!')
#             return redirect('category_builder')
#         else:
#             print(form.errors)

#     else:
#         form = CategoryForm()
#     context = {
#         'form': form,
#     }
#     return render(request, 'vendor/add_category.html', context)


# @login_required(login_url='login')
# @user_passes_test(check_role_vendor)
# def edit_category(request, pk=None):
#     category = get_object_or_404(Category, pk=pk)
#     if request.method == 'POST':
#         form = CategoryForm(request.POST, request.FILES, instance=category)
#         if form.is_valid():
#             category_name = form.cleaned_data['category_name']
#             category = form.save(commit=False)
#             category.vendor = get_vendor(request)
#             category.slug = slugify(category_name)
#             form.save()
#             messages.success(request, 'Category updated successfully!')
#             return redirect('category_builder')
#         else:
#             print(form.errors)

#     else:
#         form = CategoryForm(instance=category)
#     context = {
#         'form': form,
#         'category': category,
#     }
#     return render(request, 'vendor/edit_category.html', context)


# @login_required(login_url='login')
# @user_passes_test(check_role_vendor)
# def delete_category(request, pk=None):
#     category = get_object_or_404(Category, pk=pk)
#     category.delete()
#     messages.success(request, 'Category has been deleted successfully!')
#     return redirect('category_builder')




#*  ================ Sub Category section =============== 

@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def subcategory_builder(request, pk=None):
    vendor = get_vendor(request)
    # Fetch the main category by primary key (pk) and ensure it belongs to the vendor
    category = get_object_or_404(Category, pk=pk)
    # Fetch subcategories for the specified category
    subcategories = Category.objects.filter(parent=category, vendor_subcategory_reference_id=vendor.id).order_by('created_at')
    
    context = {
        'category': category,
        'subcategories': subcategories,
    }
    return render(request, 'vendor/fooditems_by_category.html', context)

@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def add_sub_category(request, category_id=None):
    vendor = get_vendor(request)
    main_category = None

    try:
        # Fetch the main category if a category_id is provided
        if category_id:
            main_category = Category.objects.filter(id=category_id, parent=None).first()
            if not main_category:
                messages.error(request, "Main category not found.")
                return redirect('category_builder')

        if request.method == 'POST':
            form = SubCategoryForm(request.POST, request.FILES, vendor=vendor)
            if form.is_valid():
                try:
                    subcategory = form.save(commit=False)
                    subcategory.vendor_subcategory_reference_id = vendor.id
                    subcategory.parent = main_category
                    subcategory.category_code = f"SUB-{slugify(subcategory.category_name)}-{main_category.category_code}-{vendor.id}"
                    subcategory.slug = slugify(f"{subcategory.category_name}{main_category}{vendor.id}")
                    subcategory.save()

                    messages.success(request, 'Subcategory added successfully!')
                    return redirect('category_builder')
                except Exception as e:
                    print(e)
                    messages.error(request, "An error occurred while saving the subcategory. Please ensure you're not creating a duplicate, and try again.")
                    form = SubCategoryForm(vendor=vendor, initial={'parent': main_category})


            else:
                messages.error(request, "Please correct the errors below.")
        else:
            form = SubCategoryForm(vendor=vendor, initial={'parent': main_category})

    except Exception as e:
        messages.error(request, "An unexpected error occurred. Please ensure you're not creating a duplicate, and try again.")
        # Optionally log the error: logger.error(str(e))
        return redirect('category_builder')

    context = {
        'form': form,
        'main_category': main_category,
    }
    print("line number 470")

    return render(request, 'vendor/add_sub_category.html', context)

@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def edit_subcategory(request, category_id=None, pk=None):
    try:
        subcategory = get_object_or_404(Category, pk=pk)
        vendor = get_vendor(request)

        # Fetch the main category if a category_id is provided
        main_category = Category.objects.filter(id=category_id, parent=None).first()

        # Ensure it’s a subcategory (has a parent)
        if not subcategory.parent:
            messages.error(request, "This is a main category, not a subcategory.")
            return redirect('category_builder')

        if request.method == 'POST':
            form = SubCategoryForm(request.POST, request.FILES,instance=subcategory)
            
            # Set parent field to be read-only
            form.fields['parent'].initial = subcategory.parent
            form.fields['parent'].widget.attrs['readonly'] = True

            if form.is_valid():
                try:
                    category_name = form.cleaned_data['category_name']
                    subcategory = form.save(commit=False)
                    subcategory.vendor_subcategory_reference_id = vendor.id
                    subcategory.category_code = f"SUB-{slugify(subcategory.category_name)}-{main_category.category_code}-{vendor.id}"
                    subcategory.store_type = StoreType.objects.get(name=vendor.store_type)
                    subcategory.slug = slugify(f"{subcategory.category_name}{main_category or subcategory.parent}{vendor.id}")
                    subcategory.parent = main_category or subcategory.parent  # Fallback if main_category is None
                    subcategory.save()

                    messages.success(request, 'Subcategory updated successfully!')
                    return redirect('category_builder')
                except Exception as e:
                    messages.error(request, "An error occurred while updating the subcategory. Please ensure you're not creating a duplicate, and try again.")
                    # Optionally log the error: logger.error(str(e))
            else:
                messages.error(request, "Please correct the errors in the form.")
        else:
            form = SubCategoryForm(instance=subcategory, initial={'parent': subcategory.parent})
            form.fields['parent'].widget.attrs['readonly'] = True

        context = {
            'form': form,
            'subcategory': subcategory,
        }
        return render(request, 'vendor/edit_subcategory.html', context)

    except Exception as e:
        print(e)
        messages.error(request, "An unexpected error occurred. Please try again.")
        # Optionally log the error: logger.error(str(e))
        return redirect('category_builder')
    

@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def delete_subcategory(request, pk=None):
    subcategory = get_object_or_404(Category, pk=pk, parent__isnull=False)  # Ensure it's a subcategory
    vendor=get_vendor(request)
    if subcategory.vendor_subcategory_reference_id == vendor.id :  # Check if the subcategory belongs to the vendor
        subcategory.delete()
        messages.success(request, 'Subcategory deleted successfully!')
    else:
        messages.error(request, 'You are not authorized to delete this subcategory.')
    
    return redirect('category_builder')  # Redirect to the category builder page



#*  ================ Prouduct section =============== 
def product_list_view(request):
    vendor = get_vendor(request)
    products = Product.objects.filter(vendor=vendor).order_by('-id')
    context = {
        'products': products,
    }
    return render(request, 'vendor/products_list.html', context)

def get_subcategories(request, category_id):
    vendor = get_vendor(request)
    subcategories = Category.objects.filter(parent_id=category_id,vendor_subcategory_reference_id=vendor.id)
    subcategory_list = [{'id': subcategory.id, 'name': subcategory.category_name} for subcategory in subcategories]
    return JsonResponse({'subcategories': subcategory_list})
    
@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def add_product(request):
    vendor_id = request.user.user.id
    vendor = get_vendor(request)

    ProductGalleryFormSet = modelformset_factory(ProductGallery, form=ProductGalleryForm, extra=3, max_num=3)
    try:
        if request.method == 'POST':
            form = ProductForm(request.POST, request.FILES, vendor_id=vendor_id)
            formset = ProductGalleryFormSet(request.POST, request.FILES, queryset=ProductGallery.objects.none())
            if form.is_valid() and formset.is_valid():
                product = form.save(commit=False)
                product.vendor = get_vendor(request)
                # Generate the slug from the product name
                product.slug = slugify(product.product_name)
                product.save()
                # Save the images from the formset
                for form in formset:
                    if form.cleaned_data.get('image'):
                        gallery = form.save(commit=False)
                        gallery.product = product
                        gallery.save()
                messages.success(request, 'Product added successfully!')
                return redirect('vendor_products_list')
        else:
            form = ProductForm(vendor_id=vendor_id)
            formset = ProductGalleryFormSet(queryset=ProductGallery.objects.none())

        # Pass categories to the template for the dropdown
        categories = Category.objects.filter(parent__isnull=True, store_type=vendor.store_type)  # Top-level categories
        context = {
            'form': form,
            'categories': categories,
            'formset': formset
        }
        return render(request, 'vendor/add_product.html', context)

    except Exception as e:
        messages.error(request, f"An error occurred: {e}")
        return redirect('vendor_products_list')



@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def edit_product(request, product_id):
    vendor = get_vendor(request)
    product = get_object_or_404(Product, id=product_id, vendor=get_vendor(request))
    # Create a formset for managing gallery images
    ProductGalleryFormSet = modelformset_factory(
        ProductGallery,
        form=ProductGalleryForm,
        extra=1,  # Allow one extra form for uploading a new image
        can_delete=True  # Allow existing images to be deleted
    )
    try :
        if request.method == 'POST':
            form = EditProductForm(request.POST, request.FILES, instance=product,vendor_id = vendor.id)
            formset = ProductGalleryFormSet(
                request.POST, request.FILES, queryset=ProductGallery.objects.filter(product=product)
            )
            if form.is_valid() and formset.is_valid():
                product = form.save(commit=False)
                product.slug = slugify(product.product_name)
                product.save()

                # Process gallery formset
                for form in formset:
                    if form.cleaned_data.get('DELETE'):
                        instance = form.instance
                        # Ensure instance exists and has an ID before deleting
                        if instance and instance.id:
                            instance.delete()
                    elif form.cleaned_data.get('image'):
                        # Save new or updated image
                        gallery = form.save(commit=False)
                        gallery.product = product
                        gallery.save()
                messages.success(request, 'Product updated successfully!')
                return redirect('vendor_products_list')
            else:
                print('error')
                print(formset.errors)
        else:
            form = EditProductForm(instance=product,vendor_id = vendor.id)
            formset = ProductGalleryFormSet(queryset=ProductGallery.objects.filter(product=product))

        categories = Category.objects.filter(parent__isnull=True,store_type=vendor.store_type)  # Top-level categories
        context = {
            'form': form,
            'categories': categories,
            'product': product,
            'formset': formset,
        }
        return render(request, 'vendor/edit_product.html', context)
    except Exception as e:
        messages.error(request, f"An error occurred: {e}")
        return redirect('vendor_products_list')

@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def delete_product(request, product_id=None):
    product = get_object_or_404(Product, id=product_id)
    if product.vendor == get_vendor(request):  # Ensure the product belongs to the vendor
        product.delete()
        messages.success(request, 'Product deleted successfully!')
    else:
        messages.error(request, 'You are not authorized to delete this product.')
    
    return redirect('vendor_products_list')  # Redirect to the product list page



@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def add_food(request):
    if request.method == 'POST':
        form = FoodItemForm(request.POST, request.FILES)
        if form.is_valid():
            foodtitle = form.cleaned_data['food_title']
            food = form.save(commit=False)
            food.vendor = get_vendor(request)
            food.slug = slugify(foodtitle)
            form.save()
            messages.success(request, 'Food Item added successfully!')
            return redirect('fooditems_by_category', food.category.id)
        else:
            print(form.errors)
    else:
        form = FoodItemForm()
        # modify this form
        form.fields['category'].queryset = Category.objects.filter(vendor=get_vendor(request))
    context = {
        'form': form,
    }
    return render(request, 'vendor/add_food.html', context)



@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def edit_food(request, pk=None):
    food = get_object_or_404(FoodItem, pk=pk)
    if request.method == 'POST':
        form = FoodItemForm(request.POST, request.FILES, instance=food)
        if form.is_valid():
            foodtitle = form.cleaned_data['food_title']
            food = form.save(commit=False)
            food.vendor = get_vendor(request)
            food.slug = slugify(foodtitle)
            form.save()
            messages.success(request, 'Food Item updated successfully!')
            return redirect('fooditems_by_category', food.category.id)
        else:
            print(form.errors)

    else:
        form = FoodItemForm(instance=food)
        form.fields['category'].queryset = Category.objects.filter(vendor=get_vendor(request))
    context = {
        'form': form,
        'food': food,
    }
    return render(request, 'vendor/edit_food.html', context)


@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def delete_food(request, pk=None):
    food = get_object_or_404(FoodItem, pk=pk)
    food.delete()
    messages.success(request, 'Food Item has been deleted successfully!')
    return redirect('fooditems_by_category', food.category.id)


def opening_hours(request):
    opening_hours = OpeningHour.objects.filter(vendor=get_vendor(request))
    form = OpeningHourForm()
    context = {
        'form': form,
        'opening_hours': opening_hours,
    }
    return render(request, 'vendor/opening_hours.html', context)


def add_opening_hours(request):
    # handle the data and save them inside the database
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == 'POST':
            day = request.POST.get('day')
            from_hour = request.POST.get('from_hour')
            to_hour = request.POST.get('to_hour')
            is_closed = request.POST.get('is_closed')
            
            try:
                hour = OpeningHour.objects.create(vendor=get_vendor(request), day=day, from_hour=from_hour, to_hour=to_hour, is_closed=is_closed)
                if hour:
                    day = OpeningHour.objects.get(id=hour.id)
                    if day.is_closed:
                        response = {'status': 'success', 'id': hour.id, 'day': day.get_day_display(), 'is_closed': 'Closed'}
                    else:
                        response = {'status': 'success', 'id': hour.id, 'day': day.get_day_display(), 'from_hour': hour.from_hour, 'to_hour': hour.to_hour}
                return JsonResponse(response)
            except IntegrityError as e:
                response = {'status': 'failed', 'message': from_hour+'-'+to_hour+' already exists for this day!'}
                return JsonResponse(response)
        else:
            HttpResponse('Invalid request')


def remove_opening_hours(request, pk=None):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            hour = get_object_or_404(OpeningHour, pk=pk)
            hour.delete()
            return JsonResponse({'status': 'success', 'id': pk})


def order_detail(request, order_number):
    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_food = OrderedFood.objects.filter(order=order, product__vendor=get_vendor(request))
        # Just pick the first status of the vendor's ordered food
        vendor_status = ordered_food.first().status if ordered_food.exists() else 'Processing'
        tax_data = json.loads(order.tax_data)

        # Check if all items are Paid or Completed
        all_paid = all(item.status in ['Paid', 'Completed'] for item in ordered_food)

        context = {
            'order': order,
            'ordered_food': ordered_food,
            'vendor_status': vendor_status,
            'subtotal': order.get_total_by_vendor()['subtotal'],
            'tax_data': order.get_total_by_vendor()['tax_dict'],
            'grand_total': order.get_total_by_vendor()['grand_total'],
            'tax_data': tax_data,
            'vendor': get_vendor(request),
            'all_paid': all_paid,
        }
    except:
        return redirect('vendor')
    return render(request, 'vendor/order_detail.html', context)


def my_orders(request):
    vendor = Vendor.objects.get(user=request.user)
    orders = Order.objects.filter(vendors__in=[vendor.id], is_ordered=True).order_by('-updated_at')
    context = {
        'orders': orders,
    }
    return render(request, 'vendor/my_orders.html', context)


def order_status(request):
    if request.method == "POST":
        status = request.POST.get('order_status')
        order_number = request.POST.get('order_number')

        try:
            order = Order.objects.get(order_number=order_number)

            vendor = Vendor.objects.get(user=request.user)

            ordered_products = OrderedFood.objects.filter(order = order, product__vendor = vendor)

            if not ordered_products.exists():
                return JsonResponse({'error': 'No items found for this vendor in the order.'})
            
            for item in ordered_products:
                product = item.product
                prev_status = item.status

                # Stock adjustment
                if prev_status not in ['Cancelled', 'Refunded'] and status in ['Cancelled', 'Refunded']:
                    product.qty += item.quantity
                elif prev_status not in ['Paid', 'Completed', 'Processing'] and status in ['Paid', 'Completed', 'Processing']:
                    product.qty -= item.quantity

                product.save()
                item.status = status
                item.save()
            mail_subject = f'Order #{order_number} - Items from {vendor.vendor_name} updated to {status}'
            message = f"""
            Dear {order.user.first_name},<br><br>
            The items you ordered from <strong>{vendor.vendor_name}</strong> in order #{order_number} are now marked as <strong>{status}</strong>.<br><br>
            Thank you,<br>
            Flickbasket
            """
            recipient = order.user.email
            from_email = settings.DEFAULT_FROM_EMAIL
            mail = EmailMessage(mail_subject, message, from_email, to=[recipient])
            mail.content_subtype = "html"
            mail.send()

            return JsonResponse({'message': 'Vendor items updated successfully.', 'status': status})

        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found.'})
            
    return JsonResponse({'error': 'Invalid request'})






# def order_status(request):
#     if request.method == "POST":
#         status = request.POST.get('order_status')
#         order_number = request.POST.get('order_number')
#         try:
#             order = Order.objects.get(order_number=order_number)
#             ordered_products = OrderedFood.objects.filter(order=order)
#             if order.status not in ['Cancelled', 'Refunded'] and status in ['Cancelled','Refunded']:
#                 print("we are in cancel")
#                 print(ordered_products)
#                 for single_ordered_product in ordered_products:
#                     product = Product.objects.get(id=single_ordered_product.product.id)
#                     product.qty+=single_ordered_product.quantity
#                     product.save()
#                     print("Product", product)
#                     print(single_ordered_product.quantity)
#                     print(product.qty)
#             if order.status not in ['Paid', 'Completed', 'Processing'] and status in ['Paid', 'Completed', 'Processing']:
#                  print("current status ", order.status)
#                  for single_ordered_product in ordered_products:
#                     product = Product.objects.get(id=single_ordered_product.product.id)
#                     product.qty-=single_ordered_product.quantity
#                     product.save()
#                     print("Product", product)
#                     print(single_ordered_product.quantity)
#                     print(product.qty)
            
 
#             order.status = status 
#             order.save()
#             # Send email 
#             mail_subject = f'Your Order #{order_number} is {status}'
#             message = f"""
#             Dear {order.user.first_name},
            
#             Your order with ID #{order_number} has been marked as {status}.
#             <br>
#             Thank you for shopping with us.
            
#             <br><br>
#             Regards,
#             Flickbasket
#         """
#             recipient = order.user.email
#             from_email = settings.DEFAULT_FROM_EMAIL
#             # Send the email
#             mail = EmailMessage(mail_subject, message, from_email, to=[recipient])
#             mail.content_subtype = "html"
#             mail.send()
            
#             return JsonResponse({'message': 'Status updated successfully.', 'status': order.status})
#         except Order.DoesNotExist:
#             return JsonResponse({'error': 'Order not found.'})
#     return JsonResponse({'error': 'Invalid request'})


def media_library(request):
    vendor = Vendor.objects.get(user=request.user)
    images = MediaUpload.objects.filter(vendor=vendor)
    for image in images:
        # Build absolute URL for each image
        image.absolute_url = request.build_absolute_uri(image.image.url)

    if request.method == "POST":
        selected_images = request.POST.getlist('images')
        if selected_images:
            MediaUpload.objects.filter(id__in=selected_images).delete()
            return redirect('media_library')
    context = {'images': images}
    return render(request, 'vendor/media_library.html', context)


@method_decorator(csrf_exempt, name='dispatch')
class FileUploadView(View):
    def post(self, request, *args, **kwargs):
        # Get files from request.FILES
        vendor = Vendor.objects.get(user=request.user)
        files = request.FILES.getlist('file')  # Dropzone sends files as 'file'
        for f in files:
            MediaUpload.objects.create(image=f, vendor=vendor)
        return JsonResponse({'message': 'Files uploaded successfully!'})
    

def import_your_data(request):
    return render(request, 'vendor/import_your_data.html')


def connect_erp(request):
    source = request.GET.get('source')
    if source == 'Custom':
        return redirect('upload_csv')
    
    context = {
        'source': source,
    }
    return render(request, 'vendor/connect_erp.html', context)


def upload_csv(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            decoded_file = file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.reader(io_string)
            headers = next(reader)

            request.session['csv_data'] = decoded_file  # Save for later processing
            request.session['csv_filename'] = file.name

            return redirect('map_headers')  # Redirect to map headers page
    else:
        form = CSVUploadForm()
    return render(request, 'vendor/upload_csv.html', {'form': form})


def map_headers(request):
    csv_data = request.session.get('csv_data')
    filename = request.session.get('csv_filename')
    vendor=get_vendor(request)
    if not csv_data or not filename :
        return redirect('upload_csv')
    print("filename", filename)

    io_string = io.StringIO(csv_data)
    reader = csv.reader(io_string)
    headers = next(reader)
    first_data_row = next(reader, [])
    
    internal_fields = CSV_FIELD_MAPPINGS

    return render(request, 'vendor/map_headers.html', {
        'csv_headers': headers,
        'internal_fields': internal_fields,
        'csv_filename': filename,
        'sample_row': first_data_row,
        'vendor':vendor.id
    })

    

def process_mapped_data(request):
    if request.method == 'POST':
        mappings = {}
        for key in CSV_FIELD_MAPPINGS.keys():
            mapped_header = request.POST.get(f'mapping_{key}')
            if mapped_header:
                mappings[key] = mapped_header
        request.session['mappings'] = mappings
    else:
        mappings = request.session.get('mappings', {})

    csv_data = request.session.get('csv_data')
    if not csv_data or not mappings:
        return redirect('upload_csv')

    io_string = io.StringIO(csv_data)
    reader = csv.DictReader(io_string)
    products = []
    errors = []
    error_rows = set()
    error_fields_for_frontend = []

    for idx, row in enumerate(reader, start=1):
        product = {}
        missing_fields = []
        field_errors = []
        for internal_field, csv_header in mappings.items():
            value = row.get(csv_header, '').strip() if csv_header else ''
            product[internal_field] = value

            field_cfg = CSV_FIELD_MAPPINGS[internal_field]
            label = field_cfg['label']
            optional = field_cfg.get('optional', False)
            typ = field_cfg.get('type')

            # Required field check
            if not value and not optional:
                missing_fields.append(label)
                print(f"Missing field: {label} in row {idx}")
                error_fields_for_frontend.append({'row': idx, 'field': internal_field})
                continue
            # Type checks for non-empty values
            if value:
                if typ == 'decimal':
                    try:
                        decimal.Decimal(value)
                    except Exception:
                        field_errors.append(f"{label} must be a number (e.g. 12.99)")
                elif typ == 'int':
                    try:
                        int(value)
                    except ValueError:
                        field_errors.append(f"{label} must be a whole number (e.g. 15)")
            # print("field_cfg=====>", internal_field)
            if value and internal_field == 'category':
                cat_vendor = get_vendor(request)
                categories = Category.objects.filter(store_type=cat_vendor.store_type)
                # print('categories==>', categories)

                if not categories.filter(category_name__iexact=value).exists():
                    field_errors.append(f"{label} must be the correct category based on your store type.")
                    error_fields_for_frontend.append({'row': idx, 'field': internal_field})




        # Gather errors
        if missing_fields or field_errors:
            error_rows.add(idx - 1)
            messages = []
            if missing_fields:
                messages.append("Missing value for " + ", ".join(missing_fields))
            messages.extend(field_errors)
            errors.append({'row': idx, 'messages': messages})
        product['orig_idx'] = idx - 1
        products.append(product)

    request.session['products'] = products
    request.session['errors'] = errors  # Save errors for error-only view

    show_all = request.GET.get('show_all') == '1'
    errors_only = request.GET.get('errors_only') == '1'
    field_mappings_filtered = {k: CSV_FIELD_MAPPINGS[k] for k in mappings.keys()}
    if 'image' in field_mappings_filtered:
        # Move 'image' to the start
        field_mappings_filtered = {'image': field_mappings_filtered['image'], **{k: v for k, v in field_mappings_filtered.items() if k != 'image'}}

    if errors_only:
        filtered_products = []
        for idx, p in enumerate(products):
            if idx in error_rows:
                filtered_products.append(p)
        count = len(filtered_products)
    else:
        filtered_products = products
        count = len(products)

    if show_all:
        page_number = request.GET.get('page', 1)
        per_page = 20
        paginator = Paginator(filtered_products, per_page)
        try:
            page_obj = paginator.page(page_number)
        except Exception:
            page_obj = paginator.page(1)
        products_to_display = page_obj.object_list
        offset = (page_obj.number - 1) * per_page
    else:
        products_to_display = filtered_products[:5]
        page_obj = None
        paginator = None
        offset = 0
    
    # print("misssing fields=====>>>", missing_fields)
    # print("misssing fields=====>>>", error_fields_for_frontend)
    # print("errro ===>>>", errors)
    # print("error row fields=====>>>", error_rows)

    if len(error_rows) == 0 and len(errors) == 0 and len(error_fields_for_frontend) == 0:
        vendor = get_vendor(request)
        save_to_clone_products_table(request, products, vendor)
        massage_helper.messages.success(request, "Products have been validated successfully.")

    return render(request, 'vendor/validate_import_data.html', {
        'products': products_to_display,
        'field_mappings': field_mappings_filtered,
        'count': count,
        'show_all': show_all,
        'errors': errors,
        'error_rows': error_rows,
        'offset': offset,
        'page_obj': page_obj,
        'paginator': paginator,
        'errors_only': errors_only,
        'error_fields': error_fields_for_frontend 
    })

def validate_import_data(request):
    pass

def set_image_to_mapped_data(request):
    if request.method == 'POST':
        session_products = request.session.get('products', [])
        mappings = request.session.get('mappings', {})
        vendor = get_vendor(request)

        if not session_products:
            messages.error(request, "No product data available. Please upload and validate your CSV first.")
            return redirect('upload_csv')

        # Fetch existing products for this vendor from DB
        existing_products = ProductCloneTable.objects.filter(vendor=vendor)
        existing_product_map = {
            (p.product_name.strip().lower()): p.image_url
            for p in existing_products if p.image_url
        }

        updated_products = []

        for product in session_products:
            product_name = product.get('product_name', '').strip()
            if not product_name:
                continue  # Skip products without a name

            existing_image_url = product.get('image', '').strip()

            # If image already present in session, skip
            if existing_image_url:
                updated_products.append(product)
                continue

            # Check if DB product has an image
            existing_image_from_db = existing_product_map.get(product_name.lower())
            if existing_image_from_db:
                product['image'] = existing_image_from_db
                updated_products.append(product)
                continue

            # Otherwise, try to generate
            image_url = search_images(request, product_name)
            if image_url:
                product['image'] = image_url
                # Update DB as well
                try:
                    clone_product = ProductCloneTable.objects.get(vendor=vendor, product_name=product_name)
                    clone_product.image_url = image_url
                    clone_product.save()
                except ProductCloneTable.DoesNotExist:
                    pass  # Skip if not yet saved to DB
            else:
                messages.warning(request, f"No image found for product: {product_name}")
            
            updated_products.append(product)

        # Save updated session data
        request.session['products'] = updated_products
        if 'image' not in mappings:
            mappings['image'] = 'image'
        request.session['mappings'] = mappings

        return redirect('process_mapped_data_with_images')

    return redirect('upload_csv')


def search_images(request, product_name):
    print("im called")
 
    if product_name:
        url = (
            f"https://www.googleapis.com/customsearch/v1"
            f"?q={product_name}&cx={settings.GOOGLE_CX_ID}&searchType=image"
            # f"&rights=cc_publicdomain|cc_attribute"  # License filter for legal reuse
            f"&key={settings.GOOGLE_API_KEYS}&num=1"
        )
        response = requests.get(url)
        data = response.json()
        print("data", data)
        return data.get("items", [{}])[0].get("link", "")  # Return the first image link if available





def process_mapped_data_with_images(request):
    products = request.session.get('products', [])
    mappings = request.session.get('mappings', {})
    # print("mappings", mappings)
    # print("products", products)
    
    show_all = request.GET.get('show_all') == '1'
    field_mappings_filtered = {k: CSV_FIELD_MAPPINGS[k] for k in mappings.keys()}
    if 'image' in field_mappings_filtered:
        # Move 'image' to the start
        field_mappings_filtered = {'image': field_mappings_filtered['image'], **{k: v for k, v in field_mappings_filtered.items() if k != 'image'}}

    if show_all:
        page_number = request.GET.get('page', 1)
        per_page = 20
        paginator = Paginator(products, per_page)
        try:
            page_obj = paginator.page(page_number)
        except Exception:
            page_obj = paginator.page(1)
        products_to_display = page_obj.object_list
        offset = (page_obj.number - 1) * per_page
    else:
        products_to_display = products[:5]
        page_obj = None
        paginator = None
        offset = 0
    messages.success(request, f"Products images generated successfully.")
    return render(request, 'vendor/validate_import_data.html', {
        'products': products_to_display,
        'field_mappings': field_mappings_filtered,
        'count': len(products),
        'show_all': show_all,
        'offset': offset,
        'page_obj': page_obj,
        'paginator': paginator,
        'SaveToDatabase': True,
    })






def download_image_to_field(product_obj, image_url):
    print("image_url", image_url)
    print("image function enter ")
    if not image_url:
        return
    try:
        main_image_filename = image_url.split('/')[-1].split("?")[0]
        response = requests.get(image_url, timeout=10)
        if response.status_code == 200:
            main_content_file = ContentFile(response.content, name=main_image_filename)
            print("Downloaded image:", main_image_filename)
            product_obj.image.save(main_image_filename, main_content_file, save=False)
        else:
            print(f"Image download failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"Image download error: {e}")

def safe_decimal(val, default=Decimal(0), field_name=None):
    try:
        print("typeof val", field_name, type(val))
        val = str(val).strip()
        return Decimal(val) if val not in (None, '', '-') else default
    except Exception:
        return default
def save_to_database(request):
    if request.method != 'POST':
        return HttpResponse("Invalid request method.")

    products = request.session.get('products', [])
    mappings = request.session.get('mappings', {})

    if not products or not mappings:
        messages.error(request, "No data to save. Please upload a CSV file and map the headers first.")
        return redirect('upload_csv')

    vendor = get_vendor(request)
    errors = []
    row_num = 1
    success_count = 0

    with transaction.atomic():
        for row in products:
            try:
                product_name = row.get('product_name', '').strip()
                if not product_name:
                    errors.append(f"Row {row_num}: Product name is required.")
                    continue
                regular_price = safe_decimal(row.get('regular_price',0), 'regular_price')
                tax_category_name = row.get('tax_category', '').strip()
                tax_percentage = int(row.get('tax_percentage', '').strip())
                category_name = row.get('category','').strip()
                subcategory_name = row.get('subcategory', '').strip()
                image_url = row.get('image', '').strip()

                # Category lookup/creation (same as before)
                try:
                    category_obj = Category.objects.get(category_name__iexact=category_name)
                except Category.DoesNotExist:
                    messages.error(request,"Please enter the correct category based on your store type.")
                    return redirect('import_your_data')

                subcategory_obj = None
                if subcategory_name:
                    category_code = f"SUB-{slugify(subcategory_name)}-{category_obj.category_code}-{vendor.id}"
                    try:
                        subcategory_obj = Category.objects.get(
                            category_name=subcategory_name,
                            parent=category_obj,
                            vendor_subcategory_reference_id=vendor.id,
                            category_code=category_code,
                        )
                    except Category.DoesNotExist:
                        subcategory_obj = Category.objects.create(
                            category_name=subcategory_name.strip(),
                            parent=category_obj,
                            vendor_subcategory_reference_id=vendor.id,
                            category_code=category_code,
                            slug=slugify(f"{subcategory_name}{category_obj}{vendor.id}")
                        )

                try:
                    tax_category_obj = Tax.objects.filter(tax_category=tax_category_name, tax_percentage=tax_percentage).first()
                    if not tax_category_obj:
                        tax_category_obj = Tax.objects.create(
                        tax_category=tax_category_name,
                        tax_percentage=tax_percentage,
                        tax_desc=''
                        )
                        tax_category_obj.save()
                        print(f"Tax category '{tax_category_name}' with {tax_percentage}% created.")
                except Tax.DoesNotExist:
                    messages.error(request, f"Tax category '{tax_category_name}' not found. Skipping product '{product_name}'.")
                    continue

                deposit_category_obj = DepositCategory.objects.filter(deposit_category__iexact='Clickmall').first()
                cost_price = safe_decimal(row.get('cost_price', 0), 'cost_price')
                qty = safe_decimal(row.get('qty',  0),'qty')
                sales_price_val = row.get('sales_price',  0)
                sales_price = safe_decimal(sales_price_val, None, 'sales_price')

                slug_val = slugify(product_name)

                # --- UPSERT LOGIC START ---
                product_obj = None
                try:
                   
                    product_obj = Product.objects.get(vendor=vendor, slug=slug_val)
                    if vendor and row.get('barcode','').strip():
                        if Product.objects.filter(vendor=vendor, barcode=row.get('barcode','').strip()).exists():
                            ex_bar_product = Product.objects.filter(vendor=vendor, barcode=row.get('barcode','').strip()).first()
                            if ex_bar_product.product_name != product_obj.product_name:
                                errors.append(f"Your given barcode is already used in {ex_bar_product.product_name} . Please use unique barcode for {product_name}")
                                row_num += 1
                                continue
                    # Update existing
                    product_obj.product_name = product_name
                    product_obj.product_desc = row.get('description', '').strip()
                    product_obj.full_specification = row.get('full_specification', '').strip()
                    product_obj.hsn_number = row.get('hsn_number','').strip()
                    product_obj.model_number = row.get('model_number','').strip()
                    product_obj.cost_price = cost_price
                    product_obj.regular_price = regular_price
                    product_obj.sales_price = sales_price
                    product_obj.is_available = True
                    product_obj.category = category_obj
                    product_obj.subcategory = subcategory_obj
                    product_obj.is_popular = False
                    product_obj.is_top_collection = False
                    product_obj.is_active = True
                    product_obj.barcode = row.get('barcode','').strip() or None
                    product_obj.qty = qty
                    product_obj.tax_category = tax_category_obj
                    product_obj.deposit_category = deposit_category_obj
                    product_obj.unit_type = row.get('unit_type','pcs').strip() or 'pcs'
                    product_obj.company = row.get('company', '').strip() or None
                    product_obj.product_size = row.get('product_size','').strip() or None
                except Product.DoesNotExist:
                    if vendor and row.get('barcode','').strip():
                        if Product.objects.filter(vendor=vendor, barcode=row.get('barcode','').strip()).exists():
                            product = Product.objects.filter(vendor=vendor, barcode=row.get('barcode','').strip()).first()
                            errors.append(f"Your given barcode is already used in {product.product_name} . Please use unique barcode for {product_name}")
                            row_num += 1
                            continue
                    # Create new
                    product_obj = Product(
                        vendor=vendor,
                        product_name=product_name,
                        slug=slug_val,
                        product_desc=row.get('description', '').strip(),
                        full_specification=row.get('full_specification', '').strip(),
                        hsn_number=row.get('hsn_number','').strip(),
                        model_number=row.get('model_number','').strip(),
                        cost_price=cost_price,
                        regular_price=regular_price,
                        sales_price=sales_price,
                        is_available=True,
                        category=category_obj,
                        subcategory=subcategory_obj,
                        is_popular=False,
                        is_top_collection=False,
                        is_active=True,
                        barcode=row.get('barcode','').strip() or None,
                        qty=qty,
                        tax_category=tax_category_obj,
                        deposit_category=deposit_category_obj,
                        unit_type=row.get('unit_type','pcs').strip() or 'pcs',
                        company=row.get('company', '').strip() or None,
                        product_size=row.get('product_size','').strip() or None,
                    )
                # --- UPSERT LOGIC END ---

                download_image_to_field(product_obj, image_url)
                product_obj.save()
                success_count += 1
                row_num += 1
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                row_num += 1

    if success_count:
        messages.success(request, f"{success_count} products imported successfully.")

    if errors:
        for error in errors:
            print("error", error)
            messages.error(request, error)

    return redirect('import_your_data')



def update_image_url_in_session(request):
    vendor=get_vendor(request)
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            row_id = int(data.get("row_id", -1))
            new_url = data.get("new_url", "")
            products = request.session.get("products", [])
            if 0 <= row_id < len(products):
                products[row_id]["image"] = new_url
                print(new_url)
                print(products[row_id])
                product_name = products[row_id]['product_name']
                product = ProductCloneTable.objects.get(product_name=product_name, vendor=vendor)
                product.image_url = new_url
                product.save()
                print(product.image_url)
                request.session["products"] = products
                return JsonResponse({"success": True})
            else:
                return JsonResponse({"success": False, "error": "Invalid row id"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)
    return JsonResponse({"success": False, "error": "Bad request"}, status=400)





def save_to_clone_products_table(request, products, vendor):
    try:
        bulk_objs = []
        seen_slugs = set()  # To avoid duplicate slugs within this bulk

        for row in products:
            try:
                product_name = row.get('product_name', '').strip()
                if not product_name:
                    continue

                slug = slugify(product_name)
                key = (vendor.id, slug)

                # Skip if already seen in this loop
                if key in seen_slugs:
                    continue

                # Skip if already in DB
                if ProductCloneTable.objects.filter(vendor=vendor, slug=slug).exists():
                    continue

                seen_slugs.add(key)

                bulk_objs.append(ProductCloneTable(
                    vendor=vendor,
                    slug=slug,
                    product_name=product_name,
                    regular_price=row.get('regular_price', 0),
                    image_url=row.get('image', ''),
                    category_name=row.get('category', ''),
                    qty=row.get('qty', 0),
                    tax_category_name=row.get('tax_category', ''),
                    deposit_category_name=row.get('deposit_category', ''),
                    unit_type=row.get('unit_type', 'pcs'),
                ))

            except:
                # Skip this row if any error occurs while processing it
                continue

        if bulk_objs:
            try:
                ProductCloneTable.objects.bulk_create(bulk_objs)
            except:
                # Silently skip bulk_create error
                pass

    except:
        # Silently skip unexpected top-level error
        pass