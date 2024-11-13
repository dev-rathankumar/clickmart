from unicodedata import category
from urllib import response
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.db import IntegrityError

from menu.forms import CategoryForm, FoodItemForm, SubCategoryForm, ProductForm,EditProductForm
from orders.models import Order, OrderedFood
from menu.models import Product
import vendor
from .forms import VendorForm, OpeningHourForm
from accounts.forms import UserProfileForm

from accounts.models import UserProfile
from .models import OpeningHour, Vendor
from django.contrib import messages

from django.contrib.auth.decorators import login_required, user_passes_test
from accounts.views import check_role_vendor
from menu.models import Category, FoodItem
from django.template.defaultfilters import slugify


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
        if profile_form.is_valid() and vendor_form.is_valid():
            profile_form.save()
            vendor_form.save()
            messages.success(request, 'Settings updated.')
            return redirect('vprofile')
        else:
            print(profile_form.errors)
            print(vendor_form.errors)
    else:
        profile_form = UserProfileForm(instance = profile)
        vendor_form = VendorForm(instance=vendor)

    context = {
        'profile_form': profile_form,
        'vendor_form': vendor_form,
        'profile': profile,
        'vendor': vendor,
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
        form = CategoryForm(request.POST)
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
        form = CategoryForm(request.POST, instance=category)
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
    products = Product.objects.filter(vendor=vendor)
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
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = get_vendor(request)
            # Generate the slug from the product name
            product.slug = slugify(product.product_name)
            product.save()
            messages.success(request, 'Product added successfully!')
            return redirect('vendor_products_list')
    else:
        form = ProductForm()

    # Pass categories to the template for the dropdown
    categories = Category.objects.filter(parent__isnull=True)  # Top-level categories
    context = {
        'form': form,
        'categories': categories,
    }
    return render(request, 'vendor/add_product.html', context)
def view_Product(request, pk=None):
    # Get the main product
    product = get_object_or_404(Product, id=pk)
    
    # Fetch similar products from the same category, excluding the current product
    similar_products = Product.objects.filter(
        category=product.category,
        is_available=True  # Optional: Only include available products
    ).exclude(id=product.id)
    
    context = {
        'product': product,
        'similar_products': similar_products,
    }
    
    return render(request, 'vendor/product_view.html', context)
@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, vendor=get_vendor(request))
    if request.method == 'POST':
        form = EditProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            product.slug = slugify(product.product_name)
            product.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('vendor_products_list')
    else:
        form = EditProductForm(instance=product)

    categories = Category.objects.filter(parent__isnull=True)  # Top-level categories
    context = {
        'form': form,
        'categories': categories,
        'product': product,
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
    orders = Order.objects.filter(vendors__in=[vendor.id], is_ordered=True).order_by('created_at')

    context = {
        'orders': orders,
    }
    return render(request, 'vendor/my_orders.html', context)