# from django.db import models
# from vendor.models import Vendor
# from unified.models import Product
# from inventory.models import tax as Tax
# from django.db.models import JSONField

# # Inward Invoice Feature
# class Supplier(models.Model):
#     vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
#     name = models.CharField(max_length=100)
#     gstin = models.CharField(max_length=15, null=True, blank=True)

# class InwardInvoice(models.Model):
#     vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
#     supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
#     invoice_number = models.CharField(max_length=50)
#     invoice_date = models.DateField()
#     total_amount = models.DecimalField(max_digits=12, decimal_places=2)
#     cgst = models.DecimalField(max_digits=12, decimal_places=2)
#     sgst = models.DecimalField(max_digits=12, decimal_places=2)
#     igst = models.DecimalField(max_digits=12, decimal_places=2)
#     created_at = models.DateTimeField(auto_now_add=True)

# class InwardInvoiceItem(models.Model):
#     invoice = models.ForeignKey(InwardInvoice, on_delete=models.CASCADE)
#     product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
#     product_snapshot = JSONField(null=True, blank=True)  # stores full product info as JSON
#     quantity = models.IntegerField()
#     gst_percent = models.DecimalField(max_digits=5, decimal_places=2)
#     cgst = models.DecimalField(max_digits=12, decimal_places=2)
#     sgst = models.DecimalField(max_digits=12, decimal_places=2)
#     igst = models.DecimalField(max_digits=12, decimal_places=2)
#     amount = models.DecimalField(max_digits=12, decimal_places=2)


# # GST Module feature 
# class GSTTaxStructure(models.Model):
#     tax = models.OneToOneField(Tax, on_delete=models.CASCADE)
#     cgst = models.DecimalField(max_digits=5, decimal_places=2)
#     sgst = models.DecimalField(max_digits=5, decimal_places=2)
#     igst = models.DecimalField(max_digits=5, decimal_places=2)

#     def __str__(self):
#         return f"Structure for {self.tax.name}"


# # Sales Invoice Model 
# class SalesInvoice(models.Model):
#     SALE_TYPE_CHOICES = (
#         ('B2B', 'Business to Business'),
#         ('B2C', 'Business to Consumer'),
#         ('EXPORT', 'Export'),
#     )
#     invoice_number = models.CharField(max_length=50, unique=True)
#     vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
#     customer_name = models.CharField(max_length=100, blank=True)
#     customer_gstin = models.CharField(max_length=15, blank=True, null=True)
#     sale_type = models.CharField(max_length=10, choices=SALE_TYPE_CHOICES)
#     date = models.DateField()
#     total_amount = models.DecimalField(max_digits=12, decimal_places=2)
#     cgst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
#     sgst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
#     igst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#        return self.invoice_number
   