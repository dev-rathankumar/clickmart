import json
from django.db import models
from accounts.models import User
from unified.models import Product
from vendor.models import Vendor
import re
from decimal import Decimal

request_object = ''

def decimal_to_float(value):
    """Helper function to convert Decimal to float."""
    if isinstance(value, Decimal):
        return float(value)
    return value

def preprocess_val(val):
    """Function to replace Decimal instances in the string with float values."""
    # Replace 'Decimal("x.y")' with 'x.y'
    val = re.sub(r'Decimal\("(\d+\.\d+)"\)', r'\1', val)
    return val


class Payment(models.Model):
    PAYMENT_METHOD = (
        ('PayPal', 'PayPal'),
        ('RazorPay', 'RazorPay'), # Only for Indian Students.
        ('COD', 'COD'), # Only for Indian Students.
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=100)
    payment_method = models.CharField(choices=PAYMENT_METHOD, max_length=100)
    amount = models.CharField(max_length=50)
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.transaction_id


class Order(models.Model):
 
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    vendors = models.ManyToManyField(Vendor, blank=True)
    order_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=50)
    address = models.CharField(max_length=200)
    country = models.CharField(max_length=15, blank=True)
    state = models.CharField(max_length=15, blank=True)
    city = models.CharField(max_length=50)
    pin_code = models.CharField(max_length=10)
    total = models.FloatField()
    tax_data = models.JSONField(blank=True, help_text = "Data format: {'tax_type':{'tax_percentage':'tax_amount'}}", null=True)
    total_data = models.JSONField(blank=True, null=True)
    total_tax = models.FloatField()
    payment_method = models.CharField(max_length=25)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Concatenate first name and last name
    @property
    def name(self):
        return f'{self.first_name} {self.last_name}'

    def order_placed_to(self):
        return ", ".join([str(i) for i in self.vendors.all()])


    def get_total_by_vendor(self):
        try:
            vendor = Vendor.objects.get(user=request_object.user)
        except Vendor.DoesNotExist:
            print("Vendor does not exist for the current user.")
            return {
                'subtotal': 0,
                'tax_dict': {},
                'grand_total': 0,
            }

        if not self.total_data:
            # If total_data is None or empty, return zero values
            return {
                'subtotal': 0,
                'tax_dict': {},
                'grand_total': 0,
            }

        try:
            # Load the total_data as a list
            total_data_list = json.loads(self.total_data)
        except json.JSONDecodeError as e:
            print(f"JSON decoding error in total_data: {e}")
            return {
                'subtotal': 0,
                'tax_dict': {},
                'grand_total': 0,
            }

        subtotal = 0
        tax = 0
        tax_dict_list = []  # Store each tax dict separately
        processed_taxes = set()  # Track processed tax entries to avoid duplication

        # Iterate over each item in the list
        for total_data in total_data_list:
            # Get vendor-specific data from the dictionary
            data = total_data.get(str(vendor.id))
            if not data:
                continue  # Skip if no data for this vendor

            # Iterate through subtotal/tax data
            for key, val in data.items():
                try:
                    # Try converting the key (which should be subtotal) to float
                    subtotal += float(key)
                except ValueError as e:
                    print(f"Error converting subtotal key to float: {e}")
                    continue

                if isinstance(val, str):
                    # Replace single quotes to double quotes for JSON compatibility
                    val = val.replace("'", '"')
                    # Preprocess to handle Decimal values
                    val = preprocess_val(val)
                    
                    try:
                        # Parse JSON safely
                        parsed_val = json.loads(val)
                    except json.JSONDecodeError as e:
                        print(f"JSON decoding error: {e} in val: {val}")
                        continue  # Skip processing if JSON error

                    # Check if parsed_val is a list or a single dictionary
                    if isinstance(parsed_val, dict):
                        tax_dict_list.append(parsed_val)  # If it's a dict, add it directly
                    elif isinstance(parsed_val, list) and all(isinstance(item, dict) for item in parsed_val):
                        tax_dict_list.extend(parsed_val)  # If it's a list of dicts, extend the list
                    else:
                        print("Unexpected format after parsing:", parsed_val)
                        continue
                else:
                    print("Unexpected format in val:", val)
                    continue

                # Calculate tax from parsed data
                for tax_entry in tax_dict_list:
                    tax_entry_tuple = tuple((tax_name, tuple(sorted(tax_info.items()))) for tax_name, tax_info in tax_entry.items())
                    
                    if tax_entry_tuple in processed_taxes:
                        # Skip if this tax entry was already processed
                        continue
                        
                    processed_taxes.add(tax_entry_tuple)
                    
                    for tax_name, tax_info in tax_entry.items():
                        for rate, amount in tax_info.items():
                            tax += float(decimal_to_float(amount))

        # Compile the final context
        # grand_total = float(subtotal) + float(tax)
        grand_total = float(subtotal)
        print("processed_taxes:", processed_taxes)  

        context = {
            'subtotal': subtotal,
            'tax_dict': tax_dict_list,  # Now stores a list of tax dictionaries
            'grand_total': grand_total,
        }

        return context

    def __str__(self):
        return self.order_number

class OrderedFood(models.Model):
    STATUS = (
        ('Processing', 'Processing'),
        ('Paid', 'Paid'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('Refunded', 'Refunded'),
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.FloatField()
    amount = models.FloatField()
    status = models.CharField(max_length=15, choices=STATUS, default='Processing')
    variant_info = models.JSONField(blank=True, null=True, help_text="Snapshot of variant details at the time of order")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ordered Product"
        verbose_name_plural = "Ordered Products"

    def __str__(self):
        return self.product.product_name