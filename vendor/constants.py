
CSV_FIELD_MAPPINGS = {
     'image': {
        'label': 'Image',
        'help': 'Optional: The image file of the product.',
        'optional': True,
        'type': 'str',  # Assuming you handle file uploads separately
    },
    'product_name': {
        'label': 'Product Name',
        'help': 'The name of the product.',
        'optional': False,
        'type': 'str',
        
    },
    'category': {
        'label': 'Category',
        'help': 'The main category under which this product falls.',
        'optional': False,
        'type': 'str',
        
    },
    'subcategory': {
        'label': 'Subcategory',
        'help': 'Optional: A more specific subcategory.',
        'optional': True,
        'type': 'str',
    },
    'cost_price': {
        'label': 'Cost Price',
        'help': 'Optional: The price you purchased this product at.',
        'optional': True,
        'type': 'decimal',
    },
    'regular_price': {
        'label': 'MRP',
        'help': 'The Maximum Retail Price (MRP) for the customer.',
        'optional': False,
        'type': 'decimal',
    },
    'sale_price': {
        'label': 'Sale Price',
        'help': 'Optional: The price at which the product is currently being sold.',
        'optional': True,
        'type': 'decimal',
    },
    'qty': {
        'label': 'Available Quantity',
        'help': 'The current stock quantity available for sale.',
        'optional': False,
        'type': 'int',
    },
    'hsn_number': {
        'label': 'HSN Code',
        'help': 'Optional: The 8-digit HSN code for tax purposes.',
        'optional': True,
        'type': 'str',
    },
    'barcode': {
        'label': 'Barcode',
        'help': 'Optional: Product’s barcode number (if available). Used for scanning.',
        'optional': True,
         'type': 'str',
    },
    'tax_category': {
        'label': 'Tax Category',
        'help': 'Product’s Tax Category (if not available: NA).',
        'optional': False,
        'type': 'str',
    },
    'tax_percentage': {
        'label': 'Tax Percentage',
        'help': 'Product’s Tax Percentage (if not available: 0).',
        'optional': False,
        'type': 'int',
    },
    'product_desc': {
        'label': 'Description',
        'help': 'Optional: A short description of the product',
       'optional': True,
       'type': 'str',
    },
    'full_specification': {
        'label': 'Full Specification',
        'help': 'Optional: Detailed specifications of the product.',
        'optional': True,
        'type': 'str',
    },
    'model_number': {
        'label': 'Model Number',
        'help': 'Optional: The model number of the product.',
        'optional': True,
        'type': 'str',
    },
    'unit_type': {
        'label': 'Unit Type',
        'help': 'Optional: The type of the product.(Default:pcs)',
        'optional': True,
        'type': 'str',
    },
    'company': {
        'label': 'Company',
        'help': 'Optional: The name of the company that makes the product.',
        'optional': True,
        'type': 'str',
    },
    'product_size': {
        'label': 'Product Size',
        'help': 'Optional: The size of the product, like small, medium, or large.',
        'optional': True,
        'type': 'str',
    },
   
}

