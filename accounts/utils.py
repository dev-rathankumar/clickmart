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
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
import os
import io
from django.conf import settings
from django.contrib.staticfiles import finders
import textwrap
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.enums import TA_RIGHT
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


# def generate_receipt_pdf(order, ordered_food, tax_data):
#     """
#     Generate a PDF receipt for the given order with tax data and product details.
#     Returns the PDF file as an in-memory byte stream.
#     """
#     buffer = io.BytesIO()
#     p = canvas.Canvas(buffer, pagesize=letter)

#     # Absolute paths for static assets
#     unpaid_abs_path = finders.find('images/upaid.png')  # Replace with .png


#     # Fetch the vendor details (assuming there's only one vendor)
#     vendor = order.vendors.first()  # Fetch the first vendor
#     print(f'{vendor.user_profile.profile_picture}')
#     if vendor.user_profile.profile_picture:
#         vendor_logo_path = os.path.join(settings.MEDIA_ROOT, str(vendor.user_profile.profile_picture))
#     else:
#         vendor_logo_path = None

#     page_width, page_height = letter  # 612x792 points

#     # Add Vendor Logo
#     try:
#         if vendor_logo_path:  # Ensure the path exists
#             p.drawImage(vendor_logo_path, 50, page_height - 100, width=200, height=90, mask='auto')
#         else:
#             print("Vendor logo not found, skipping.")
#     except Exception as e:
#         print(f"Error adding vendor logo: {e}")

#     # Add Header (Centered text)
#     p.setFont("Helvetica-Bold", 18)
#     p.drawString(50, page_height - 120, "Thank You For Your Order")

#     # Add Order and Vendor Details
#     p.setFont("Helvetica", 12)
#     p.drawString(50, page_height - 150, f"Store Name: {vendor.vendor_name}")
#     p.drawString(50, page_height - 165, f"Store Phone: {vendor.user.phone_number}")
#     p.drawString(50, page_height - 180, f"Order Date: {order.created_at.strftime('%b %d, %Y, %I:%M %p')}")
#     p.drawString(300, page_height - 180, f"Order No: {order.order_number}")
#     p.drawString(50, page_height - 195, f"Payment Method: {order.payment_method}")
#     p.drawString(300, page_height - 195, f"Transaction ID: {order.payment.transaction_id}")

#     # Add logo on the left corner
#     try:
#         if unpaid_abs_path:  # Ensure the path is not None
#             p.drawImage(unpaid_abs_path, 300, page_height - 310, width=200, height=110, mask='auto')
#         else:
#             print("Unpaid image not found.")
#     except Exception as e:
#         print(f"Error adding unpaid image: {e}")
#     # Customer Info (Centered text)
#     p.setFont("Helvetica-Bold", 12)
#     p.drawString(50, page_height - 220, f"Hello {order.name},")
#     p.setFont("Helvetica", 10)
#     p.drawString(50, page_height - 240, f"Review your order details below.")
#     p.drawString(50, page_height - 255, f"Address: {order.address}")
#     p.drawString(50, page_height - 270, f"Email: {order.email}")

#     # Product Table Header (Centered text)
#     y = page_height - 330
#     p.setFont("Helvetica-Bold", 10)
#     p.drawString(50, y, "Product")
#     p.drawString(295, y, "Quantity")
#     p.drawString(380, y, "Price")
#     y -= 20

#     # Ordered Products and Tax Details
#     p.setFont("Helvetica", 10)
#     # Adding tax details
#     total_gst = 0  # Initialize total GST variable
#     for item in ordered_food:
#         p.drawString(50, y, item.product.product_name)
#         p.drawString(300, y, str(item.quantity))

#         # Draw the rupee symbol image before the price
#         p.drawString(385, y, f"INR {item.product.sales_price or item.product.regular_price}")
#         y -= 15

#         # Iterate through tax data and render individual GST details
#         for single_tax_dict in tax_data:
#             if item.product.id == single_tax_dict['product_id']:
#                 for key, value in single_tax_dict['tax_info'].items():
#                     if value:
#                         total_gst += value  # Add value to total GST
#                         y -= -2
#                         p.setFont("Helvetica", 7)
#                         p.drawString(385, y, f"GST: INR {value:.2f}")
#                         p.setFont("Helvetica", 10)
#                         y -= 20
#     p.setLineWidth(0.4)  # A thinner line for sections
#     p.line(45, y - 10, 500, y - 10)
#     y -= 15
#     # Total Summary (Centered text)
#     p.setFont("Helvetica-Bold", 10)
#     y -= 15
#     # Display Total GST
#     if total_gst > 0:
#         p.drawString(52, y, f"Total GST:")
#         p.drawString(385, y, f"INR {total_gst:.2f}")
#         y -= 15
#     # Grand Total
#     formatted_grand_total = "{:.2f}".format(order.total)

#     # Use `formatted_grand_total` in the PDF
#     p.drawString(52, y, f"Grand Total:")
#     p.drawString(385, y, f"INR {formatted_grand_total}")
#     y -= 40
#     # Footer
#     y -= 50
#     p.setFont("Helvetica", 10)
#     p.drawString(50, y, "Thank you for your order!")
#     p.drawString(50, y - 15, "Need help? Call +91 0011223344")

#     # Finalize PDF
#     p.showPage()
#     p.save()
#     buffer.seek(0)
#     return buffer

def truncate_text(text, max_length=20):
    return (text[:max_length - 3] + "...") if len(text) > max_length else text

def extract_variant(product_variant_info):
    try:
        if not product_variant_info:
            return ""
        attributes = product_variant_info.get("attributes", [])
        # Extract attribute values and join with " / "
        values = [attr.get("value", "") for attr in attributes]
        if values:
            return f"[{' / '.join(values)}] "
        return ""
    except Exception:
        return ""
def generate_receipt_pdf(order, ordered_food, tax_data):
  
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=50, bottomMargin=30)
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    bold = ParagraphStyle("Bold", parent=normal, fontName="Helvetica-Bold")
    # New styles with larger font
    large_bold = ParagraphStyle(name="LargeBold", fontSize=14, leading=16, spaceAfter=5, alignment=TA_LEFT)
    larger_bold = ParagraphStyle(name="LargerBold", fontSize=12, leading=14, spaceAfter=5)
    story = []

    # Vendor Info (left) and Customer Info (right) as two columns
    vendor = order.vendors.first()
    vendor_info = [
        Paragraph(f"<b>{vendor.vendor_name}</b>", large_bold),
        Paragraph(f"Phone: {vendor.user.phone_number}", normal),
        Paragraph(f"Order Date: {order.created_at.strftime('%b %d, %Y, %I:%M %p')}", normal),
        Paragraph(f"Order No: {order.order_number}", normal),
        Paragraph(f"Transaction ID: {order.payment.transaction_id}", normal),
        Paragraph(f"GSTIN. {vendor.gst_number}", normal) if vendor and vendor.gst_number else "",
        Paragraph(f"Email: {vendor.user.email}", normal),
    ]
    customer_info = [
        Paragraph(f"<b>Billed To:</b>", larger_bold),
        Paragraph(f"{order.name}", normal),
        Paragraph(f"Address:{order.address}", normal),
        Paragraph(f"{order.email}", normal),
        Paragraph(f"Phone: {order.phone}", normal),
    ]

    # Remove empty lines
    vendor_info = [v for v in vendor_info if v]
    customer_info = [c for c in customer_info if c]

    # Header Table (2 columns)
    header_table = Table(
        [[vendor_info, customer_info]],
        colWidths=[400, 150]
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        # no grid
    ]))
    story.append(header_table)
    story.append(Spacer(1, 18))

    # Product Table
    data = [["#", "Product", "HSN Number", "Model Number", "Quantity", "Price", "Tax", "Total"]]
    total_gst = 0
    item_total_price = 0
    item_total_qty = 0
    for idx, item in enumerate(ordered_food, start=1):
        product_name = f"{extract_variant(item.variant_info)}{truncate_text(item.product.product_name)}"
        product_hsn_number = item.product.hsn_number
        product_model_number = item.product.model_number
        quantity = item.quantity
        price = item.product.sales_price or item.product.regular_price
        item_total = price * quantity
        item_total_price += price
        item_total_qty += quantity

        wrapped_product_name = Paragraph(product_name, normal) if product_name else ''
        wrapped_product_hsn_number = Paragraph(product_hsn_number, normal) if product_hsn_number else ''
        wrapped_product_model_number = Paragraph(product_model_number, normal) if product_model_number else ''

        gst_value = 0
        for single_tax_dict in tax_data:
            if item.product.id == single_tax_dict['product_id']:
                for key, value in single_tax_dict['tax_info'].items():
                    if value:
                        gst_value += value
                        total_gst += value

        data.append([
            str(idx), wrapped_product_name, wrapped_product_hsn_number, wrapped_product_model_number,
            str(quantity), f"INR {price:.2f}", f"INR {gst_value:.2f}", f"INR {item_total}"
        ])
    data.append(["", "", "", "Total", f"{item_total_qty}", f"INR {item_total_price:.2f}", f"INR {total_gst:.2f}", f"INR {order.total:.2f}"])

    # Table
    table = Table(data, colWidths=[30, 120, 70, 70, 50, 70, 65, 90])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
    ])
    table.setStyle(style)
    story.append(table)
    story.append(Spacer(1, 24))

    # Totals and UNPAID image in a right-aligned "footer" table
    unpaid_abs_path = finders.find('images/upaid.png')
    unpaid_img = Image(unpaid_abs_path, width=200, height=110) if unpaid_abs_path else ''
    right_aligned = ParagraphStyle(
        name='RightAlign',
        fontSize=10,
        alignment=TA_RIGHT,
        spaceAfter=0,
        spaceBefore=0  # or just alignment=2
    )

    bold_right_aligned = ParagraphStyle(
        name='BoldRightAlign',
        fontSize=10,
        leading=11,
        alignment=TA_RIGHT,
        spaceAfter=0,
        spaceBefore=0
    )
    totals = [
        [unpaid_img,  # left cell (image)
         Paragraph(f"Total Tax: INR {total_gst:.2f}", right_aligned)],
        ["", Paragraph(f"Total (Tax included): INR {order.total:.2f}", right_aligned)],
        ["", Paragraph(f"<b>Grand Total: {order.total:.2f}</b>", bold_right_aligned)],
    ]
    footer_table = Table(
        totals,
        colWidths=[300, 200],
        hAlign='RIGHT'
    )
    # Set table style
  
    footer_table.setStyle(TableStyle([
        # Add line above Grand Total
        ("LINEABOVE", (1, 2), (1, 2), 1, colors.black),

        # Vertical and horizontal alignment
        ("VALIGN", (0, 0), (0, -1), "TOP"),        # image column
        ("VALIGN", (0, 0), (1, -1), "BOTTOM"),     # right column (text)

        # ✅ Right-align all cells in second column
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),

        # Optional: adjust paddings
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(footer_table)

    doc.build(story)
    buffer.seek(0)
    return buffer