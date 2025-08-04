from django.db import models
from vendor.models import Vendor
from unified.models import Product

# Create your models here.

class Supplier(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    gstin = models.CharField(max_length=15, null=True, blank=True)

class InwardInvoice(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    invoice_number = models.CharField(max_length=50)
    invoice_date = models.DateField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    cgst = models.DecimalField(max_digits=12, decimal_places=2)
    sgst = models.DecimalField(max_digits=12, decimal_places=2)
    igst = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

class InwardInvoiceItem(models.Model):
    invoice = models.ForeignKey(InwardInvoice, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2)
    cgst = models.DecimalField(max_digits=12, decimal_places=2)
    sgst = models.DecimalField(max_digits=12, decimal_places=2)
    igst = models.DecimalField(max_digits=12, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
