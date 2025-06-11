


# your_app/constants.py

CSV_FIELD_MAPPINGS = {
    'product_name': {
        'label': 'Product Name',
        'help': 'The name of the product.',
    },
    'category': {
        'label': 'Category',
        'help': 'The main category under which this product falls.',
    },
    'subcategory': {
        'label': 'Subcategory',
        'help': 'Optional: A more specific subcategory.',
    },
    'cost_price': {
        'label': 'Cost Price',
        'help': 'Optional: The price you purchased this product at.',
    },
    'regular_price': {
        'label': 'MRP',
        'help': 'The Maximum Retail Price for the customer.',
    },
    'qty': {
        'label': 'Available Qty',
        'help': 'The current stock quantity available for sale.',
    },
    'hsn_number': {
        'label': 'HSN Code',
        'help': 'Optional: The 8-digit HSN code for tax purposes.',
    },
    'barcode': {
        'label': 'Barcode',
        'help': 'Optional: Product’s barcode number (if available). Used for scanning.',
    },
}

