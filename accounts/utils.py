from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage, message
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.core.files.storage import default_storage
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.templatetags.static import static
import os
import io
from django.contrib.staticfiles import finders


# from orders.models import OrderedFood 
def detectUser(user):
    if user.role == 1:
        redirectUrl = 'vendorDashboard'
        return redirectUrl
    elif user.role == 2:
        redirectUrl = 'custDashboard'
        return redirectUrl
    elif user.role == None and user.is_superuser:
        redirectUrl = '/admin'
        return redirectUrl

    
def send_verification_email(request, user, mail_subject, email_template):
    from_email = settings.DEFAULT_FROM_EMAIL
    current_site = get_current_site(request)
    message = render_to_string(email_template, {
        'user': user,
        'domain': current_site,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
    })
    to_email = user.email
    mail = EmailMessage(mail_subject, message, from_email, to=[to_email])
    mail.content_subtype = "html"
    mail.send()


def send_notification(mail_subject, mail_template, context,pdf_file=None):
    from_email = settings.DEFAULT_FROM_EMAIL
    message = render_to_string(mail_template, context)
    if(isinstance(context['to_email'], str)):
        to_email = []
        to_email.append(context['to_email'])
    else:
        to_email = context['to_email']
    mail = EmailMessage(mail_subject, message, from_email, to=to_email)
    mail.content_subtype = "html"
    if pdf_file:
        mail.attach(f"Invoice_{context['order'].order_number}.pdf", pdf_file.read(), 'application/pdf')
        mail.send()
    else:
        mail.send()


def generate_receipt_pdf(order, ordered_food, tax_data):
    """
    Generate a PDF receipt for the given order with tax data and product details.
    Returns the PDF file as an in-memory byte stream.
    """
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    # Absolute paths for static assets
    unpaid_abs_path = finders.find('images/upaid.png')  # Replace with .png


    # Fetch the vendor details (assuming there's only one vendor)
    vendor = order.vendors.first()  # Fetch the first vendor
    print(f'{vendor.user_profile.profile_picture}')
    if vendor.user_profile.profile_picture:
        vendor_logo_path = os.path.join(settings.MEDIA_ROOT, str(vendor.user_profile.profile_picture))
    else:
        vendor_logo_path = None

    page_width, page_height = letter  # 612x792 points

    # Add Vendor Logo
    try:
        if vendor_logo_path:  # Ensure the path exists
            p.drawImage(vendor_logo_path, 50, page_height - 100, width=200, height=90, mask='auto')
        else:
            print("Vendor logo not found, skipping.")
    except Exception as e:
        print(f"Error adding vendor logo: {e}")

    # Add Header (Centered text)
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, page_height - 120, "Thank You For Your Order")

    # Add Order and Vendor Details
    p.setFont("Helvetica", 12)
    p.drawString(50, page_height - 150, f"Store Name: {vendor.vendor_name}")
    p.drawString(50, page_height - 165, f"Store Phone: {vendor.user.phone_number}")
    p.drawString(50, page_height - 180, f"Order Date: {order.created_at.strftime('%b %d, %Y, %I:%M %p')}")
    p.drawString(300, page_height - 180, f"Order No: {order.order_number}")
    p.drawString(50, page_height - 195, f"Payment Method: {order.payment_method}")
    p.drawString(300, page_height - 195, f"Transaction ID: {order.payment.transaction_id}")

    # Add logo on the left corner
    try:
        if unpaid_abs_path:  # Ensure the path is not None
            p.drawImage(unpaid_abs_path, 300, page_height - 310, width=200, height=110, mask='auto')
        else:
            print("Unpaid image not found.")
    except Exception as e:
        print(f"Error adding unpaid image: {e}")
    # Customer Info (Centered text)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, page_height - 220, f"Hello {order.name},")
    p.setFont("Helvetica", 10)
    p.drawString(50, page_height - 240, f"Review your order details below.")
    p.drawString(50, page_height - 255, f"Address: {order.address}")
    p.drawString(50, page_height - 270, f"Email: {order.email}")

    # Product Table Header (Centered text)
    y = page_height - 330
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, "Product")
    p.drawString(295, y, "Quantity")
    p.drawString(380, y, "Price")
    y -= 20

    # Ordered Products and Tax Details
    p.setFont("Helvetica", 10)
    # Adding tax details
    total_gst = 0  # Initialize total GST variable
    for item in ordered_food:
        p.drawString(50, y, item.product.product_name)
        p.drawString(300, y, str(item.quantity))

        # Draw the rupee symbol image before the price
        p.drawString(385, y, f"INR {item.product.sales_price or item.product.regular_price}")
        y -= 15

        # Iterate through tax data and render individual GST details
        for single_tax_dict in tax_data:
            if item.product.id == single_tax_dict['product_id']:
                for key, value in single_tax_dict['tax_info'].items():
                    if value:
                        total_gst += value  # Add value to total GST
                        y -= -2
                        p.setFont("Helvetica", 7)
                        p.drawString(385, y, f"GST: INR {value:.2f}")
                        p.setFont("Helvetica", 10)
                        y -= 20
    p.setLineWidth(0.4)  # A thinner line for sections
    p.line(45, y - 10, 500, y - 10)
    y -= 15
    # Total Summary (Centered text)
    p.setFont("Helvetica-Bold", 10)
    y -= 15
    # Display Total GST
    if total_gst > 0:
        p.drawString(52, y, f"Total GST:")
        p.drawString(385, y, f"INR {total_gst:.2f}")
        y -= 15
    # Grand Total
    formatted_grand_total = "{:.2f}".format(order.total)

    # Use `formatted_grand_total` in the PDF
    p.drawString(52, y, f"Grand Total:")
    p.drawString(385, y, f"INR {formatted_grand_total}")
    y -= 40
    # Footer
    y -= 50
    p.setFont("Helvetica", 10)
    p.drawString(50, y, "Thank you for your order!")
    p.drawString(50, y - 15, "Need help? Call +91 0011223344")

    # Finalize PDF
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer