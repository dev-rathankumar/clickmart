from urllib import response
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from marketplace.models import Cart, Tax
from marketplace.context_processors import get_cart_amounts
from menu.models import Product
from .forms import OrderForm
from .models import Order, OrderedFood, Payment
import simplejson as json
from .utils import generate_order_number, order_total_by_vendor
from accounts.utils import send_notification,generate_receipt_pdf
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.views.decorators.csrf import csrf_exempt 
from inventory.models import tax
from django.contrib import messages
from django.views.decorators.cache import never_cache





@login_required(login_url='login')
@never_cache
def place_order(request):
    if request.method == "GET":
        return redirect("checkout")
    cart_items = Cart.objects.filter(user=request.user).order_by('created_at')
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('marketplace')

    vendors_ids = []
    for i in cart_items:
        if i.product.vendor.id not in vendors_ids:
            vendors_ids.append(i.product.vendor.id)
    
    # {"vendor_id":{"subtotal":{"tax_type": {"tax_percentage": "tax_amount"}}}}
    subtotal = 0
    total_data = []
    k = {}
    items_count= 0
    for i in cart_items:
        print("i product cart items", i.product.variants)
        for v in i.product.variants.all():
            if v == i.product_variant_group:
                print("variant found", v)
        product_total = 0
        product = Product.objects.get(pk=i.product.id, vendor_id__in=vendors_ids)
        v_id = product.vendor.id
        if v_id in k:
            subtotal = k[v_id]
            if i.product_variant_group and i.product_variant_group.price is not None:
                    product_total += (i.product_variant_group.price * i.quantity)
                    subtotal += (i.product_variant_group.price * i.quantity)
            else:
                if product.sales_price is not None:
                    product_total += (product.sales_price * i.quantity)
                    subtotal += (product.sales_price * i.quantity)
                else:
                    product_total += (product.regular_price * i.quantity)
                    subtotal += (product.regular_price * i.quantity)

            k[v_id] = subtotal
            items_count+=i.quantity
        else:
            if i.product_variant_group and i.product_variant_group.price is not None:
                product_total += (i.product_variant_group.price * i.quantity)
                subtotal += (i.product_variant_group.price * i.quantity)
            else:
                if product.sales_price is not None:
                    product_total += (product.sales_price * i.quantity)
                    subtotal += (product.sales_price * i.quantity)
                else:
                    product_total += (product.regular_price * i.quantity)
                    subtotal += (product.regular_price * i.quantity)
            k[v_id] = subtotal
            items_count+=i.quantity

        tax_dict = {}
        tax_instance = tax.objects.get(id=product.tax_category.id) 
        tax_amount = round((tax_instance.tax_percentage * product_total)/100, 2)
        tax_category = tax_instance.tax_category
        tax_percentage = tax_instance.tax_percentage

        tax_dict.update({tax_category: {str(tax_percentage) : tax_amount}})
        # Construct total data
        total_data.append({product.vendor.id: {str(product_total): str(tax_dict)}})
        
    

        

    subtotal = get_cart_amounts(request)['subtotal']
    total_tax = get_cart_amounts(request)['tax']
    grand_total = get_cart_amounts(request)['grand_total']
    tax_data = get_cart_amounts(request)['tax_dict']
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = Order()
            order.first_name = form.cleaned_data['first_name']
            order.last_name = form.cleaned_data['last_name']
            order.phone = form.cleaned_data['phone']
            order.email = form.cleaned_data['email']
            order.address = form.cleaned_data['address']
            order.country = form.cleaned_data['country']
            order.state = form.cleaned_data['state']
            order.city = form.cleaned_data['city']
            order.pin_code = form.cleaned_data['pin_code']
            order.user = request.user
            order.total = grand_total
            order.tax_data = json.dumps(tax_data)
            order.total_data = json.dumps(total_data)
            order.total_tax = total_tax
            order.payment_method = request.POST['payment_method']
            order.save() # order id/ pk is generated
            order.order_number = generate_order_number(order.id)
            order.vendors.add(*vendors_ids)
            order.save()
    
            context = {
                'items_count':items_count,
                'order': order,
                'cart_items': cart_items,
            }
            return render(request, 'orders/place_order.html', context)

        else:
            print(form.errors)
    return render(request, 'orders/place_order.html')


@login_required(login_url='login')
def payments(request):
        # Check if the request is ajax or not
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == 'POST':
        # STORE THE PAYMENT DETAILS IN THE PAYMENT MODEL
        order_number = request.POST.get('order_number')
        transaction_id = request.POST.get('transaction_id')
        payment_method = request.POST.get('payment_method')
        status = request.POST.get('status')

        order = Order.objects.get(user=request.user, order_number=order_number)
        payment = Payment(
            user = request.user,
            transaction_id = transaction_id,
            payment_method = payment_method,
            amount = order.total,
            status = status
        )
        payment.save()

        # UPDATE THE ORDER MODEL
        order.payment = payment
        order.is_ordered = True
        order.save()

        # MOVE THE CART ITEMS TO ORDERED Product MODEL
        cart_items = Cart.objects.filter(user=request.user)
        for item in cart_items:
            product = Product.objects.get(pk=item.product.id)
            # if product.qty < item.quantity and len(cart_items) == 1:
            #      item.delete() 
            #      return redirect('cart')
            # elif product.qty < item.quantity : 
            #     item.delete() 
            #     continue
                
            ordered_food = OrderedFood()
            ordered_food.order = order
            ordered_food.payment = payment
            ordered_food.user = request.user
            ordered_food.product = item.product
            ordered_food.quantity = item.quantity
            # DECREASE THE PRODUCT QUANTITY
            if item.product_variant_group and item.product_variant_group.stock is not None:
                ordered_food.product_variant_group = item.product_variant_group
                item.product_variant_group.stock -= item.quantity
                item.product_variant_group.save()
            else:
                product.qty -= item.quantity
                product.save()

            if item.product_variant_group and item.product_variant_group.price is not None:    
                ordered_food.price = item.product_variant_group.price
            else:
                if item.product.sales_price is not None:
                    ordered_food.price = item.product.sales_price
                else:
                    ordered_food.price = item.product.regular_price


            if item.product_variant_group and item.product_variant_group.price is not None:
                ordered_food.amount = item.product_variant_group.price * item.quantity
            else:
                if item.product.sales_price is not None:
                    ordered_food.amount = item.product.sales_price * item.quantity # total amount
                else:
                    ordered_food.amount = item.product.regular_price * item.quantity # total amount
            


            if item.product_variant_group:
                # Convert QuerySet to list of dictionaries first
                attributes = list(item.product_variant_group.attribute.all().values('attribute__name', 'value'))
                
                product_variant_info = {
                    'variant_id': item.product_variant_group.id,
                    'product_id': item.product.id,
                    'attributes': attributes,  # Now this is a list, not a QuerySet
                    'variant_price': str(item.product_variant_group.price) if item.product_variant_group.price else '',
                    'image': item.product_variant_group.image.url if item.product_variant_group.image else None,
                }
                ordered_food.variant_info =  product_variant_info
            ordered_food.save()

        # SEND ORDER CONFIRMATION EMAIL TO THE CUSTOMER
        mail_subject = 'Thank you for ordering with us.'
        mail_template = 'orders/order_confirmation_email.html'

        ordered_food = OrderedFood.objects.filter(order=order)
        customer_subtotal = 0
        for item in ordered_food:
            customer_subtotal += (item.price * item.quantity)
        tax_data = json.loads(order.tax_data)
        context = {
            'user': request.user,
            'order': order,
            'to_email': order.email,
            'ordered_food': ordered_food,
            'domain': get_current_site(request),
            'customer_subtotal': customer_subtotal,
            'tax_data': tax_data,
        }
        pdf = generate_receipt_pdf(order,ordered_food,tax_data)
        send_notification(mail_subject, mail_template, context,pdf)
        print('email sent')
        

        # SEND ORDER RECEIVED EMAIL TO THE VENDOR
        mail_subject = 'You have received a new order.'
        mail_template = 'orders/new_order_received.html'
        to_emails = []
        for i in cart_items:
            if i.product.vendor.user.email not in to_emails:
                to_emails.append(i.product.vendor.user.email)

                ordered_food_to_vendor = OrderedFood.objects.filter(order=order, product__vendor=i.product.vendor)
                context = {
                    'order': order,
                    'to_email': i.product.vendor.user.email,
                    'ordered_food_to_vendor': ordered_food_to_vendor,
                    'vendor_subtotal': order_total_by_vendor(order, i.product.vendor.id)['subtotal'],
                    'tax_data': order_total_by_vendor(order, i.product.vendor.id)['tax_dict'],
                    'vendor_grand_total': order_total_by_vendor(order, i.product.vendor.id)['grand_total'],
                }
                send_notification(mail_subject, mail_template, context)

        # CLEAR THE CART IF THE PAYMENT IS SUCCESS
        cart_items.delete()


        # RETURN BACK TO AJAX WITH THE STATUS SUCCESS OR FAILURE
        response = {
            'order_number': order_number,
            'transaction_id': transaction_id,
        }
        return JsonResponse(response)
    return HttpResponse('Payments view')


def order_complete(request):
    order_number = request.GET.get('order_no')
    transaction_id = request.GET.get('trans_id')

    try:
        order = Order.objects.get(order_number=order_number, payment__transaction_id=transaction_id, is_ordered=True)
        ordered_food = OrderedFood.objects.filter(order=order)

        subtotal = 0
        for item in ordered_food:
            subtotal += (item.price * item.quantity)

        tax_data = json.loads(order.tax_data)
        all_paid = all(item.status in ['Paid', 'Completed'] for item in ordered_food)

        context = {
            'order': order,
            'ordered_food': ordered_food,
            'subtotal': subtotal,
            'tax_data': tax_data,
            'all_paid': all_paid,
        }
        return render(request, 'orders/order_complete.html', context)
    except Exception as e:
            print("Error occurred in order_complete:")
            print(f"Order Number: {order_number}, Transaction ID: {transaction_id}")
            print(f"Error: {e}")
            return render(request, 'orders/order_failed.html', {'error': str(e)})

def generate(request):
        order = Order.objects.get(order_number=202501100237187)
        ordered_food = OrderedFood.objects.filter(order=order)
        tax_data = json.loads(order.tax_data)

        pdf_file = generate_receipt_pdf(order, ordered_food, tax_data)
        file_name = f"Invoice_{order.order_number}.pdf"
        # Create the HTTP response with PDF content
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{file_name}"'  # Use double quotes for file name

        return response