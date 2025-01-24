from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
import io
from num2words import num2words
from reportlab.pdfbase.pdfmetrics import stringWidth
from decimal import Decimal
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import textwrap

def generate_invoice_pdf(transaction, transNo):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Vendor Info
    vendor = transaction.vendor
    # Get styles
    styles = getSampleStyleSheet()
    small_style = styles["Normal"]
    small_style.fontSize = 7  
    small_style.leading = 8  

    # Header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(15, height - 50, vendor.vendor_name if vendor else "Vendor Not Available")
    c.setFont("Helvetica", 10)
    c.drawString(15, height - 70, f"Email: {vendor.user.email if vendor and vendor.user else 'N/A'}")
    c.drawString(15, height - 85, f"Phone: {vendor.user.phone_number if vendor and vendor.user else 'N/A'}")
    c.drawString(15, height - 100, f"Transaction Date: {transaction.transaction_dt.strftime('%b %d, %Y, %I:%M %p')}")
    c.drawString(15, height - 115, f"Transaction ID: {transaction.transaction_id}")
    if vendor and vendor.gst_number: 
        c.drawString(15, height - 130, f"GSTIN. {vendor.gst_number}")


    # Customer Info
    customer_info = transaction.customer_info
    c.setFont("Helvetica", 11)
    c.drawString(400, height - 50, "Billed To:")

    if customer_info and customer_info.name: 
        # Name
        c.setFont("Helvetica", 11)
        c.drawString(400, height - 65, f"Name: {customer_info.name}")
    else:
        c.setFont("Helvetica", 11)
        c.drawString(400, height - 65, f"Name: Walk-In Customer")
    # Email (conditionally displayed)
    if customer_info and customer_info.email:
        c.setFont("Helvetica", 10)
        c.drawString(400, height - 80, f"Email: {customer_info.email}")

    # Phone (conditionally displayed)
    if customer_info and customer_info.phone_number and customer_info.email == None:
        c.setFont("Helvetica", 10)
        c.drawString(400, height - 80, f"Phone: {customer_info.phone_number}")
    elif customer_info and customer_info.phone_number and customer_info.email:
        c.setFont("Helvetica", 10)
        c.drawString(400, height - 95, f"Phone: {customer_info.phone_number}")

    # Address (conditionally displayed)
    if customer_info and customer_info.phone_number and customer_info.email and customer_info.address:
        c.setFont("Helvetica", 10)
        c.drawString(400, height - 110, f"Address: {customer_info.address}")
    elif customer_info and customer_info.phone_number == None and customer_info.email == None and customer_info.address:
        c.setFont("Helvetica", 10)
        c.drawString(400, height - 80, f"Address: {customer_info.address}")
    elif customer_info and customer_info.phone_number == None and customer_info.email and customer_info.address:
        c.setFont("Helvetica", 10)
        c.drawString(400, height - 95, f"Address: {customer_info.address}")
    elif customer_info and customer_info.phone_number and customer_info.email == None and customer_info.address:
        c.setFont("Helvetica", 10)
        c.drawString(400, height - 95, f"Address: {customer_info.address}")

    # GSTIN (conditionally displayed)
    if customer_info and customer_info.phone_number and customer_info.email and customer_info.address and customer_info.gstin:
        c.setFont("Helvetica", 10)
        c.drawString(400, height - 125, f"GSTIN. {customer_info.gstin}")
    elif customer_info and customer_info.phone_number == None and customer_info.email == None and customer_info.address == None and customer_info.gstin:
        c.setFont("Helvetica", 10)
        c.drawString(400, height - 80,  f"GSTIN. {customer_info.gstin}")
    elif customer_info and customer_info.phone_number == None and customer_info.email and customer_info.address and customer_info.gstin:
        c.setFont("Helvetica", 10)
        c.drawString(400, height - 110,  f"GSTIN. {customer_info.gstin}")
    elif customer_info and customer_info.phone_number and customer_info.email == None and customer_info.address and customer_info.gstin:
        c.setFont("Helvetica", 10)
        c.drawString(400, height - 110,  f"GSTIN. {customer_info.gstin}")
    
    elif customer_info and customer_info.phone_number and customer_info.email == None and customer_info.address ==None and customer_info.gstin:
        c.setFont("Helvetica", 10)
        c.drawString(400, height - 95,  f"GSTIN. {customer_info.gstin}")
    
    elif customer_info and customer_info.phone_number==None and customer_info.email  and customer_info.address== None and customer_info.gstin:
        c.setFont("Helvetica", 10)
        c.drawString(400, height - 95,  f"GSTIN. {customer_info.gstin}")
    elif customer_info and customer_info.phone_number and customer_info.email  and customer_info.address== None and customer_info.gstin:
        c.setFont("Helvetica", 10)
        c.drawString(400, height - 110,  f"GSTIN. {customer_info.gstin}")
   
    # Code block
    data = [["#", "Product", "HSN Number", "Model Number", "Quantity", "Sales Price", "Tax", "Total"]]
    product_items = eval(transaction.products)  # Assuming `transaction.products` is serialized JSON
    regular_price_total = 0
    for idx, item in enumerate(product_items, start=1):
        product_name = item.get('name', 'N/A')
        product_hsn_number = item.get('hsn_number', 'N/A')
        product_model_number = item.get('model_number', 'N/A')
        quantity = item.get('quantity', 1)
        price = item.get('price', 0.0)
        tax_value = item.get('tax_value', 0.0)
        total_price = item.get('line_total')
        sales_price = item.get('sales_price')
        regular_price_total += Decimal(sales_price)
        unit_type = item.get('unit_type')
        tax_category = item.get('tax_category_name')
        tax_percentage = float(item.get('tax_percentage'))

        # Adjust unit type and quantity
        if unit_type == 'kg' and float(quantity) < 1:
            unit_type = 'g'
            quantity = float(quantity) * 1000
            quantity = int(quantity)
        if unit_type == 'pcs':
            quantity = int(quantity)
        elif unit_type == 'm2':
            unit_type = 'm²'
        
        # Wrap product name if it exceeds 20 characters
        wrapped_product_name = "\n".join(textwrap.wrap(product_name, width=20))
        # Define styles
        styles = getSampleStyleSheet()
        regular_style = styles['Normal']
        small_style = styles['Normal'].clone('small_style')
        small_style.fontSize = 7  # Define smaller font size
        regular_style.fontSize = 9
        small_style.leading = 8
        regular_style.leading = 8

        # Create tax details with mixed styles
        tax_details = f"INR {tax_value}<font size='6'>({tax_category} {tax_percentage:.0f}%)</font>"
        tax_paragraph = Paragraph(tax_details, regular_style)

        # Append to data
        data.append([
            str(idx), wrapped_product_name, product_hsn_number, product_model_number,
            str(quantity) + str(unit_type), f"INR {sales_price}", tax_paragraph, f"INR {total_price}"
        ])
    # Add totals
    data.append(["", "", "", "","Total",f"INR {regular_price_total:.2f}", f"INR {transaction.tax_total:.2f}", f"INR {transaction.total_sale:.2f}"])

    # Create and style the table
    table = Table(data, colWidths=[30, 110, 70, 70, 50, 70, 80, 90])

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),  # Add bold line above the Total row
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),  # Make Total row bold
    ])

    table.setStyle(style)

    # Draw Table
    table.wrapOn(c, width, height)
    table.drawOn(c, 15, height - 390)
    table_width, table_height = table.wrap(width, height)

    # Right margin
    right_margin = 25

    # Calculate Y-position for totals
    y_position = height - 360 - table_height

    # Total Section
    c.setFont("Helvetica", 10)

    # Draw "Total Tax" right-aligned
    if regular_price_total > transaction.total_sale:
        total_discount_text = f"Discount Amount:                                   INR {(regular_price_total-transaction.total_sale):.2f}"
    else: 
        total_discount_text = f"Discount Amount:                                   INR {0:.2f}"

    total_discount_width = stringWidth(total_discount_text, "Helvetica", 10)
    c.drawString(A4[0] - right_margin - total_discount_width, y_position + 15, total_discount_text)
    # Draw "Total Tax" right-aligned
    total_tax_text = f"Total Tax:                                   INR {transaction.tax_total:.2f}"
    total_tax_width = stringWidth(total_tax_text, "Helvetica", 10)
    c.drawString(A4[0] - right_margin - total_tax_width, y_position, total_tax_text)

    # Draw "Total (Tax included)" right-aligned
    total_included_text = f"Total (Tax included):                                 INR {transaction.total_sale:.2f}"
    total_included_width = stringWidth(total_included_text, "Helvetica", 10)
    c.drawString(A4[0] - right_margin - total_included_width, y_position - 15, total_included_text)

    # Draw horizontal line
    c.setLineWidth(0.5)
    c.setStrokeColor(colors.gray)
    c.line(570, y_position - 25, 240, y_position - 25)

    # Draw "Grand Total" right-aligned
    c.setFont("Helvetica-Bold", 10)
    grand_total_text = f"Grand Total:                           INR {transaction.total_sale:.2f}"
    grand_total_width = stringWidth(grand_total_text, "Helvetica-Bold", 10)
    c.drawString(A4[0] - right_margin - grand_total_width, y_position - 40, grand_total_text)

    # Draw another horizontal line
    c.setLineWidth(0.5)
    c.line(570, y_position - 50, 240, y_position - 50)

    # Set page size and margins
    page_width = A4[0]
    right_margin = 25

    # Total Sale in Words
    c.setFont("Helvetica-Bold", 12)
    total_in_words = num2words(transaction.total_sale, lang='en').capitalize()  # Capitalize the first letter
    invoice_total_text = f"Invoice Total In Words: {total_in_words} rupees only"

    # Calculate the width of the text
    text_width = stringWidth(invoice_total_text, "Helvetica-Bold", 12)

    # Calculate the X-position for right alignment
    x_position = page_width - right_margin - text_width

    # Draw the text at the calculated position
    c.drawString(x_position, y_position - 70, invoice_total_text)

   
    # Define the right margin (e.g., 20 units from the right edge of the page)
    right_margin = 25

    # Text to draw
    auth_signatory_text = "This is an electronically generated invoice, no signature is required"

    # Font and size
    font_name = "Helvetica"
    font_size = 12
    c.setFont(font_name, font_size)

    # Calculate the width of the "Authorized Signatory" text
    auth_signatory_width = stringWidth(auth_signatory_text, font_name, font_size)
    auth_signatory_x = A4[0] - right_margin - auth_signatory_width  # Align to right

    # Draw "Authorized Signatory" right-aligned
    c.drawString(auth_signatory_x, y_position - 215, auth_signatory_text)

    # Save PDF
    c.save()
    buffer.seek(0)
    return buffer
 