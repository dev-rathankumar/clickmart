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
import razorpay
from foodOnline_main.settings import RZP_KEY_ID, RZP_KEY_SECRET,PAYPAL_CLIENT_ID,PAYPAL_CLIENT_SECRET,PAYPAL_BASE_URL
from django.contrib.sites.shortcuts import get_current_site
from django.views.decorators.csrf import csrf_exempt 
from inventory.models import tax
import base64
import requests


client = razorpay.Client(auth=(RZP_KEY_ID, RZP_KEY_SECRET))



@login_required(login_url='login')
def place_order(request):
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
        product_total = 0
        product = Product.objects.get(pk=i.product.id, vendor_id__in=vendors_ids)
        v_id = product.vendor.id
        if v_id in k:
            subtotal = k[v_id]
            if product.sales_price is not None:
                product_total += (product.sales_price * i.quantity)
                subtotal += (product.sales_price * i.quantity)
            else:
                product_total += (product.regular_price * i.quantity)
                subtotal += (product.regular_price * i.quantity)

            k[v_id] = subtotal
            items_count+=i.quantity
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
            
            # RazorPay Payment
            DATA = {
                "amount": int(order.total) * 100,
                "currency": "INR",
                "receipt": "receipt #"+order.order_number,
                "notes": {
                    "key1": "value3",
                    "key2": "value2"
                }
            }
            rzp_order = client.order.create(data=DATA)
            rzp_order_id = rzp_order['id']

            context = {
                'items_count':items_count,
                'order': order,
                'cart_items': cart_items,
                'rzp_order_id': rzp_order_id,
                'RZP_KEY_ID': RZP_KEY_ID,
                'rzp_amount': float(order.total) * 100,
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

        # MOVE THE CART ITEMS TO ORDERED FOOD MODEL
        cart_items = Cart.objects.filter(user=request.user)
        for item in cart_items:
            ordered_food = OrderedFood()
            ordered_food.order = order
            ordered_food.payment = payment
            ordered_food.user = request.user
            ordered_food.product = item.product
            ordered_food.quantity = item.quantity
            # DECREASE THE PRODUCT QUANTITY
            product = Product.objects.get(pk=item.product.id)
            product.qty -= item.quantity
            product.save()
            if item.product.sales_price is not None:
                ordered_food.price = item.product.sales_price
            else:
                ordered_food.price = item.product.regular_price
            if item.product.sales_price is not None:
                ordered_food.amount = item.product.sales_price * item.quantity # total amount
            else:
                ordered_food.amount = item.product.regular_price * item.quantity # total amount

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
        print('sending notification email')
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
        print(tax_data)
        context = {
            'order': order,
            'ordered_food': ordered_food,
            'subtotal': subtotal,
            'tax_data': tax_data,
        }
        return render(request, 'orders/order_complete.html', context)
    except:
        return redirect('home')
    



# Paypal new way 



@csrf_exempt 
def create_order(request):
        
    if request.method == 'POST':
        try:
            # Generate PayPal access token (similar to generateAccessToken in server.js)

            access_token = generate_paypal_access_token() 
            grand_total = get_cart_amounts(request)['grand_total']

            # Prepare payload for PayPal order creation
            payload = {
                "intent": "CAPTURE",
                "purchase_units": [
                    {
                        "amount": {
                            "currency_code": "USD",  # Adjust currency as needed
                            "value": str(grand_total), # Assuming 'order' object is available in this view
                        },
                    }
                ],
            }

            # Make the API call to create the order
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            }
            response = requests.post("https://api-m.sandbox.paypal.com/v2/checkout/orders", headers=headers, json=payload)

            # Handle the response and return appropriate status and data
            return JsonResponse(response.json(), status=response.status_code) 

        except Exception as e:
            return JsonResponse({"error": "Failed to create order."}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)  # Handle non-POST requests


@csrf_exempt 
def capture_order(request, order_id):
    if request.method == 'POST':
        try:

            # Generate PayPal access token
            access_token = generate_paypal_access_token()

            # Make the API call to capture the order
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            }
            response = requests.post(f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture", headers=headers)


            # Handle the response and return appropriate status and data
            return JsonResponse(response.json(), status=response.status_code)
        

        except Exception as e:
            return JsonResponse({"error": "Failed to capture order."}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405) 




def generate_paypal_access_token():
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise ValueError("MISSING_API_CREDENTIALS")

    auth = base64.b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_CLIENT_SECRET}".encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "client_credentials"
    }

    response = requests.post(f"{PAYPAL_BASE_URL}/v1/oauth2/token", headers=headers, data=data)

    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Failed to generate Access Token: {response.status_code} - {response.text}")
        return None


def generate(request):
        order = Order.objects.get(order_number=202412302159143)
        ordered_food = OrderedFood.objects.filter(order=order)
        tax_data = json.loads(order.tax_data)

        pdf_file = generate_receipt_pdf(order, ordered_food, tax_data)
        file_name = f"Invoice_{order.order_number}.pdf"
        # Create the HTTP response with PDF content
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{file_name}"'  # Use double quotes for file name

        return response