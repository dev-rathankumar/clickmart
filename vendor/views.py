from django.conf import settings
from django.core.mail import EmailMessage
from unicodedata import category
from urllib import response
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.db import IntegrityError
import requests

from menu.forms import CategoryForm, FoodItemForm, ProductGalleryForm, SubCategoryForm, ProductForm,EditProductForm
from orders.models import Order, OrderedFood
# from menu.models import Product,ProductGallery
from unified.models import Product,ProductGallery
import vendor
from .forms import VendorForm, OpeningHourForm, CategoryImportForm, ProductImportForm
from accounts.forms import UserInfoForm, UserProfileForm

from accounts.models import UserProfile
from .models import OpeningHour, Vendor
from django.contrib import messages

from django.contrib.auth.decorators import login_required, user_passes_test
from accounts.views import check_role_vendor
from menu.models import Category, FoodItem
from django.template.defaultfilters import slugify
import csv
from inventory.models import tax as Tax

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from unified.models import MediaUpload

from django.forms import modelformset_factory

from django.core.files.base import ContentFile
from urllib.request import urlretrieve
from io import BytesIO
from accounts.utils import send_notification






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
    categories = Category.objects.filter(vendor=vendor, parent=None).order_by('created_at')
    context = {
        'categories': categories,
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
                category_name = row['category'].strip().replace(" ", "")
                subcategory_name = row.get('subcategory', "").strip().replace(" ", "")
                tax_category_name = row['tax_category'].strip().replace(" ", "")
                tax_percentage = row['tax_percentage'].strip().replace(" ", "")
                qty = row['stock']

                user = request.user
                vendor = Vendor.objects.get(user=user, is_approved=True)

                # Check if product with the same barcode already exists
                if Product.objects.filter(barcode=barcode , vendor=vendor).exists():
                    print(f"Product with barcode '{barcode}' already exists. Skipping product '{product_name}'.")
                    messages.error(request, f"Error processing product '{row.get('product_name', 'Unknown')}': {e}")

                # Handle ForeignKey relationships
                try:
                    category = Category.objects.get(category_name=category_name, vendor=vendor)
                except Category.DoesNotExist:
                    category = Category.objects.create(
                        category_name=category_name,
                        slug=slugify(category_name),
                        vendor=vendor,
                        description="",
                    )
                    category.save()
                    print(f"Category '{category_name}' created.")

                subcategory = None
                if subcategory_name:
                    try:
                        subcategory = Category.objects.get(category_name=subcategory_name, vendor=vendor)
                    except Category.DoesNotExist:
                        # If subcategory doesn't exist, create a new one and link to the parent category
                        subcategory = Category.objects.create(
                            category_name=subcategory_name,
                            slug=slugify(subcategory_name),
                            parent=category,  # Setting the main category as parent
                            vendor=vendor,
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


@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST,request.FILES)
        if form.is_valid():
            category_name = form.cleaned_data['category_name']
            category = form.save(commit=False)
            category.vendor = get_vendor(request)
            
            category.save() # here the category id will be generated
            category.slug = slugify(category_name)+'-'+str(category.id) # chicken-15
            category.save()
            messages.success(request, 'Category added successfully!')
            return redirect('category_builder')
        else:
            print(form.errors)

    else:
        form = CategoryForm()
    context = {
        'form': form,
    }
    return render(request, 'vendor/add_category.html', context)


@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def edit_category(request, pk=None):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            category_name = form.cleaned_data['category_name']
            category = form.save(commit=False)
            category.vendor = get_vendor(request)
            category.slug = slugify(category_name)
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('category_builder')
        else:
            print(form.errors)

    else:
        form = CategoryForm(instance=category)
    context = {
        'form': form,
        'category': category,
    }
    return render(request, 'vendor/edit_category.html', context)


@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def delete_category(request, pk=None):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    messages.success(request, 'Category has been deleted successfully!')
    return redirect('category_builder')




#*  ================ Sub Category section =============== 

@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def subcategory_builder(request, pk=None):
    vendor = get_vendor(request)
    # Fetch the main category by primary key (pk) and ensure it belongs to the vendor
    category = get_object_or_404(Category, pk=pk, vendor=vendor)
    # Fetch subcategories for the specified category
    subcategories = Category.objects.filter(vendor=vendor, parent=category).order_by('created_at')
    
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

    # Fetch the main category if a category_id is provided
    if category_id:
        main_category = Category.objects.filter(id=category_id, vendor=vendor, parent=None).first()

    if request.method == 'POST':
        form = SubCategoryForm(request.POST, vendor=vendor)
        if form.is_valid():
            subcategory = form.save(commit=False)
            subcategory.vendor = vendor
            subcategory.parent = main_category  # Set the main category as parent
            subcategory.slug = slugify(form.cleaned_data['category_name'])  # initial slug

            subcategory.save()  # Save to generate an ID
            # Update the slug with the ID appended for uniqueness
            subcategory.slug = f"{slugify(subcategory.category_name)}-{subcategory.id}"
            subcategory.save()

            messages.success(request, 'Subcategory added successfully!')
            return redirect('category_builder')
    else:
        # Pass main_category as the initial value for the parent field
        form = SubCategoryForm(vendor=vendor, initial={'parent': main_category})

    context = {
        'form': form,
        'main_category': main_category,
    }
    return render(request, 'vendor/add_sub_category.html', context)

@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def edit_subcategory(request, category_id=None, pk=None):
    subcategory = get_object_or_404(Category, pk=pk)
    vendor = get_vendor(request)

    # Fetch the main category if a category_id is provided
    main_category = Category.objects.filter(id=category_id, vendor=vendor, parent=None).first()

    # Ensure it’s a subcategory (has a parent)
    if not subcategory.parent:
        messages.error(request, "This is a main category, not a subcategory.")
        return redirect('category_builder')

    if request.method == 'POST':
        form = SubCategoryForm(request.POST, instance=subcategory)
        
        # Set parent field to be read-only but keep its value
        form.fields['parent'].initial = subcategory.parent
        form.fields['parent'].widget.attrs['readonly'] = True
        
        if form.is_valid():
            category_name = form.cleaned_data['category_name']
            subcategory = form.save(commit=False)
            subcategory.vendor = vendor
            subcategory.slug = slugify(category_name)
            subcategory.parent = main_category  # Ensure parent remains unchanged
            subcategory.save()
            messages.success(request, 'Subcategory updated successfully!')
            return redirect('category_builder')
        else:
            print(form.errors)
    else:
        # Initialize form with current subcategory data
        form = SubCategoryForm(instance=subcategory, initial={'parent': subcategory.parent})
        
        # Set parent field as read-only in the form
        form.fields['parent'].widget.attrs['readonly'] = True

    context = {
        'form': form,
        'subcategory': subcategory,
    }
    return render(request, 'vendor/edit_subcategory.html', context)

@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def delete_subcategory(request, pk=None):
    subcategory = get_object_or_404(Category, pk=pk, parent__isnull=False)  # Ensure it's a subcategory
    if subcategory.vendor == get_vendor(request):  # Check if the subcategory belongs to the vendor
        subcategory.delete()
        messages.success(request, 'Subcategory deleted successfully!')
    else:
        messages.error(request, 'You are not authorized to delete this subcategory.')
    
    return redirect('category_builder')  # Redirect to the category builder page



#*  ================ Prouduct section =============== 
def product_list_view(request):
    vendor = get_vendor(request)
    products = Product.objects.filter(vendor=vendor).order_by('-modified_date')
    context = {
        'products': products,
    }
    return render(request, 'vendor/products_list.html', context)

def get_subcategories(request, category_id):
    subcategories = Category.objects.filter(parent_id=category_id)
    subcategory_list = [{'id': subcategory.id, 'name': subcategory.category_name} for subcategory in subcategories]
    return JsonResponse({'subcategories': subcategory_list})

@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def add_product(request):
    vendor_id = request.user.user.id

    ProductGalleryFormSet = modelformset_factory(ProductGallery, form=ProductGalleryForm, extra=3, max_num=3)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES,vendor_id=vendor_id)
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
    categories = Category.objects.filter(parent__isnull=True, vendor_id = vendor_id)  # Top-level categories
    context = {
        'form': form,
        'categories': categories,
        'formset': formset
    }
    return render(request, 'vendor/add_product.html', context)





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
                    # Delete the image if marked for deletion
                    form.instance.delete()
                elif form.cleaned_data.get('image'):
                    # Save new or updated image
                    gallery = form.save(commit=False)
                    gallery.product = product
                    gallery.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('vendor_products_list')
        else:
            print('error')
            print(form.errors)
            print(formset.errors)
    else:
        form = EditProductForm(instance=product,vendor_id = vendor.id)
        formset = ProductGalleryFormSet(queryset=ProductGallery.objects.filter(product=product))

    categories = Category.objects.filter(parent__isnull=True)  # Top-level categories
    context = {
        'form': form,
        'categories': categories,
        'product': product,
        'formset': formset,
    }
    return render(request, 'vendor/edit_product.html', context)

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

        context = {
            'order': order,
            'ordered_food': ordered_food,
            'subtotal': order.get_total_by_vendor()['subtotal'],
            'tax_data': order.get_total_by_vendor()['tax_dict'],
            'grand_total': order.get_total_by_vendor()['grand_total'],
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
            order.status = status
            order.save()
            # Send email
            mail_subject = f'Your Order #{order_number} is {status}'
            message = f"""
            Dear {order.user.first_name},
            
            Your order with ID #{order_number} has been marked as {status}.
            <br>
            Thank you for shopping with us.
            
            <br><br>
            Regards,
            Clickmall
        """
            recipient = order.user.email
            from_email = settings.DEFAULT_FROM_EMAIL
            # Send the email
            mail = EmailMessage(mail_subject, message, from_email, to=[recipient])
            mail.content_subtype = "html"
            mail.send()
            
            return JsonResponse({'message': 'Status updated successfully.', 'status': order.status})
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found.'})
    return JsonResponse({'error': 'Invalid request'})


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