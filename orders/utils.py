import datetime
import simplejson as json
from decimal import Decimal
import re

def generate_order_number(pk):
    current_datetime = datetime.datetime.now().strftime('%Y%m%d%H%M%S') #20220616233810 + pk
    order_number = current_datetime + str(pk)
    return order_number


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

def order_total_by_vendor(order, vendor_id):
    try:
        # Load the total_data as a list
        total_data_list = json.loads(order.total_data)
    except json.JSONDecodeError as e:
        print(f"JSON decoding error in total_data: {e}")
        return None

    subtotal = 0
    tax = 0
    tax_dict_list = []  # Store each tax dict separately
    processed_taxes = set()  # Track processed tax entries to avoid duplication

    # Iterate over each item in the list
    for total_data in total_data_list:
        # Get vendor-specific data from the dictionary
        data = total_data.get(str(vendor_id))
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
    grand_total = float(subtotal)
    
    context = {
        'subtotal': subtotal,
        'tax_dict': tax_dict_list,  # Now stores a list of tax dictionaries
        'grand_total': grand_total,
    }

    return context