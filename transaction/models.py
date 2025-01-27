# from itertools import product
from django.db import models
from django.conf import settings
from django.db.models import F
# from inventory.models import product, PERCENTAGE_VALIDATOR
from unified.models import Product as product
from inventory.models import PERCENTAGE_VALIDATOR
import pytz
from vendor.models import Vendor
from django_ckeditor_5.fields import CKEditor5Field


timezone = pytz.timezone("Asia/Kolkata")


# Create a model for customer info for POS 
class CustomerInfo(models.Model):
    name = models.CharField(max_length=150, blank=True, null=True)
    phone_number = models.CharField(max_length=12, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    address=models.CharField(max_length=250, blank=True, null=True)
    gstin=models.CharField(max_length=50,blank=True, null=True)

    def __str__(self):
        if self.name:
            return self.name
        elif self.email:
            return self.email
        elif self.phone_number:
            return self.phone_number
        elif self.address:
            return self.address
        elif self.gstin:
            return self.gstin

# Create your models here.transaction_dt
class transaction(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, blank=True, null=True, editable=False)
    customer_info = models.ForeignKey(CustomerInfo, on_delete=models.CASCADE, blank=True, null=True, editable=False)
    date_time       = models.DateTimeField(auto_now_add=True, editable=False)
    transaction_dt  = models.DateTimeField(null=False, blank=False,editable=False)
    user            = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, null=False, blank=False, editable=False)
    transaction_id  = models.CharField(unique=True, max_length=50, null=False, editable=False)
    total_sale      = models.DecimalField(max_digits=12,decimal_places=2,null=False, editable=False)
    sub_total       = models.DecimalField(max_digits=12,decimal_places=2,null=False, editable=False)
    tax_total       = models.DecimalField(max_digits=12,decimal_places=2,null=True, editable=False)
    deposit_total   = models.DecimalField(max_digits=7,decimal_places=2,null=True, editable=False)
    payment_type    = models.CharField(choices=[('CASH','CASH'),('DEBIT/CREDIT','DEBIT/CREDIT'),('EBT','EBT')],max_length=32, null=False, editable=False)
    # receipt         = models.TextField(blank=False,null=False,editable=False)
    receipt         = CKEditor5Field(config_name='extends')
    products        = models.TextField(blank=False,null=False, editable=False)

    def __str__(self) -> str:
        return self.transaction_id

    def save(self,*args,**kwargs):
        self.transaction_dt = timezone.localize(self.transaction_dt)
        super().save(*args, **kwargs)
        for product_item in eval(self.products):
            try: item = product.objects.get(id= product_item['product_id'], vendor=self.vendor)
            except: item = product.objects.get(id= product_item['product_id'].split("_")[0])
            productTransaction.objects.create(transaction = self, transaction_id_num = self.transaction_id, transaction_date_time = self.transaction_dt,
                barcode = product_item['product_id'], name = product_item['name'], department = item.category.category_name, sales_price= product_item['sales_price'],
                qty = product_item['quantity'], cost_price = item.cost_price, tax_category = item.tax_category.tax_category,tax_percentage= item.tax_category.tax_percentage ,
                tax_amount = product_item['tax_value'], deposit_category = item.deposit_category.deposit_category,deposit = item.deposit_category.deposit_value ,
                deposit_amount = product_item['deposit_value'], payment_type= self.payment_type )
        return self

    class Meta:
        verbose_name_plural = "Transactions"


class productTransaction(models.Model):
    transaction             = models.ForeignKey("transaction", on_delete=models.RESTRICT, null=False, blank=False,editable=False,)
    transaction_id_num      = models.CharField(max_length=50, editable=False,null=False)
    transaction_date_time   = models.DateTimeField(editable=False, null=False, blank=False,)
    barcode                 = models.CharField(max_length=32, editable=False, blank = False, null=False)
    name                    = models.CharField(max_length=125, editable=False, blank = False, null = False)
    department              = models.CharField(max_length=125, editable=False,blank = False, null = True)
    sales_price             = models.DecimalField(max_digits=12, editable=False,decimal_places=2,null=False,blank = False)
    qty                     = models.DecimalField(max_digits=10, decimal_places=3, default=0, null=False, help_text="Quantity in selected unit type")
    cost_price              = models.DecimalField(max_digits=12,decimal_places=2,editable=False, default=0,null=True)
    tax_category            = models.CharField(max_length=125, editable=False,blank = False, null = False)
    tax_percentage          = models.DecimalField(max_digits=6, decimal_places=3, validators=PERCENTAGE_VALIDATOR,null=False,blank=False)
    tax_amount              = models.DecimalField(max_digits=12,decimal_places=2,editable=False, default=0,null=True)
    deposit_category        = models.CharField(max_length=125, editable=False, blank = False, null = False)
    deposit                 = models.DecimalField(max_digits=7,decimal_places=2,null=False,blank=False)
    deposit_amount          = models.DecimalField(max_digits=7,decimal_places=2,editable=False, default=0,null=True)
    payment_type            = models.CharField(max_length=32, null=False,editable=False)

    def save(self,*args,**kwargs):
        if product.objects.filter(id=self.barcode).exists():
            product.objects.filter(id=self.barcode).update(qty= F('qty')-self.qty)
        return super().save(*args, **kwargs)
    
    
    def __str__(self) -> str:
        return self.transaction_id_num + "_"+ self.barcode

    class Meta:
        verbose_name_plural = "Product Transactions"