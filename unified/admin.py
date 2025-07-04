from django.contrib import admin

from inventory.models import tax
from vendor.models import Vendor
from .models import Product as UnifieldProduct, CategoryBrowsePage, CategoryBrowseSection, ProductAssignment, SubCategoryAssignment,ProductCloneTable
from .models import ProductGallery, Category, MediaUpload
import admin_thumbnails
from import_export.admin import ImportExportModelAdmin
from import_export.admin import ExportMixin
from import_export import resources
from django.utils.html import format_html
from django import forms
from django.contrib.admin import SimpleListFilter
from dal import autocomplete
from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin

from django.contrib.admin.widgets import AutocompleteSelect

class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1


class UnifieldProductResource(resources.ModelResource):
    class Meta:
        model = UnifieldProduct
        fields = ("barcode", "vendor", "product_name", "regular_price", "sales_price", 
                  "qty", "cost_price", "image", "category", "category__category_name", 
                  "tax_category", "tax_category__tax_category", "tax_category__tax_percentage",
                  "product_desc")
        export_order = fields
        import_id_fields = ('barcode',)

    # Override dehydrate methods to show human-readable values
    def dehydrate_vendor(self, product):
        return product.vendor.vendor_name # Display vendor's name instead of ID

    def dehydrate_category(self, product):
        return product.category.category_name  # Display category name instead of ID

    def dehydrate_subcategory(self, product):
        return product.subcategory.category_name if product.subcategory else None  # Handle subcategory

    def dehydrate_tax_category(self, product):
        return product.tax_category.tax_category  # Display tax category name instead of ID

    def dehydrate_deposit_category(self, product):
        return product.deposit_category.deposit_category if product.deposit_category else None  # Handle deposit category
    
    def before_import_row(self, row, **kwargs):
        # Get Vendor by name instead of ID
        if 'vendor' in row and row['vendor']:
            vendor_name = row['vendor']
            vendor, _ = Vendor.objects.get_or_create(vendor_name=vendor_name)
            row['vendor'] = vendor.id  # Set the ForeignKey field to the actual Vendor object

        # Get Category by name instead of ID
        if 'category' in row:
            category_name = row['category']
            category = Category.objects.get(category_name=category_name)
            row['category'] = category  # Set the ForeignKey field to the actual Category object

        # Get Subcategory by name instead of ID (if exists)
        if 'subcategory' in row and row['subcategory']:
            subcategory_name = row['subcategory']
            subcategory = Category.objects.get(category_name=subcategory_name)
            row['subcategory'] = subcategory  # Set the ForeignKey field to the actual Subcategory object

        # Get TaxCategory by name instead of ID
        if 'tax_category' in row:
            tax_category_name = row['tax_category']
            tax_category = tax.objects.filter(tax_category=tax_category_name).first()
            row['tax_category'] = tax_category  # Set the ForeignKey field to the actual TaxCategory object

        # Get DepositCategory by name instead of ID (if exists)
        # if 'deposit_category' in row and row['deposit_category']:
        #     deposit_category_name = row['deposit_category']
        #     deposit_category = DepositCategory.objects.get(deposit_category=deposit_category_name)
        #     row['deposit_category'] = deposit_category  # Set the ForeignKey field to the actual DepositCategory object

        return row
    

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('category_name',)}
    list_display = ('thumbnail', 'category_name', 'category_code', 'store_type', 'vendor_subcategory_reference_id', 'updated_at', 'is_active')
    list_editable = ('store_type',)
    search_fields = ['category_name', 'category_code']
    list_filter = ('store_type', 'is_active')

    def thumbnail(self, obj):
        if obj.category_image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />', obj.category_image.url)
        return "No Image"
    thumbnail.short_description = 'Thumbnail'

class UnifieldProductAdmin(ImportExportModelAdmin):
    list_display = ['thumbnail', 'product_name', 'vendor', 'barcode', 'category', 'regular_price', 'sales_price', 'qty', 'is_popular']
    resource_class = UnifieldProductResource
    list_editable = ('is_popular',)
    list_display_links = ('product_name', 'thumbnail')
    inlines = [ProductGalleryInline]
    search_fields = ['product_name', 'slug', 'product_desc']  # 🔍 REQUIRED

    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />', obj.image.url)
        return "No Image"
    thumbnail.short_description = 'Thumbnail'

    def get_search_results(self, request, queryset, search_term):
            queryset, use_distinct = super().get_search_results(request, queryset, search_term)
            # Get the section id from the GET params (Django passes it as e.g. 'section' or 'object_id')
            section_id = request.GET.get('section') or request.GET.get('object_id')
            if section_id:
                from unified.models import CategoryBrowseSection
                try:
                    section = CategoryBrowseSection.objects.get(pk=section_id)
                    category_id = section.browse_page.category_id
                    queryset = queryset.filter(category_id=category_id)
                except CategoryBrowseSection.DoesNotExist:
                    pass
            return queryset, use_distinct
    

@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

# class ProductAdmin(admin.ModelAdmin):
#     list_display = ('product_name','is_active', 'vendor', 'is_available', 'qty')
#     inlines = [ProductGalleryInline]

class MediaUploadAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'image_thumbnail']

    def image_thumbnail(self, obj):
        return format_html('<img src="{}" width="40" height="30" />', obj.image.url)  # Adjust width and height as needed

    image_thumbnail.short_description = 'Image Thumbnail'  # Optional: change the column title


class ProductAssignmentForm(forms.ModelForm):
    class Meta:
        model = ProductAssignment
        fields = '__all__'
        widgets = {
            'product': autocomplete.ModelSelect2Multiple(
                url='product-by-category-autocomplete',
                forward=['section'],
            ),
        }
class ProductAssignmentInline(admin.TabularInline):
    model = ProductAssignment
    form = ProductAssignmentForm
    extra = 1
    max_num = 1

    class Media:
        css = {
            'all': ('admin/css/my_admin_style.css',),
        }

    # def get_formset(self, request, obj=None, **kwargs):
    #     return super().get_formset(request, obj, **kwargs)
    


class CategoryBrowsePageForm(forms.ModelForm):
    class Meta:
        model = CategoryBrowsePage
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show main categories (i.e., no parent)
        self.fields['category'].queryset = Category.objects.filter(parent__isnull=True)

#     get_category_id.short_description = "Main Category"

class SubCategoryAssignmentForm(forms.ModelForm):
    class Meta:
        model = SubCategoryAssignment
        fields = '__all__'
        widgets = {
            'subcategory': autocomplete.ModelSelect2Multiple(
                url='subcategory-by-category-autocomplete',
                forward=['section'],
            ),
        }

class SubCategoryAssignmentInline(admin.TabularInline):
    model = SubCategoryAssignment
    form = SubCategoryAssignmentForm
    extra = 1
    max_num = 1

    def get_max_num(self, request, obj=None, **kwargs):
        return 1

class MainCategoryFilter(SimpleListFilter):
    title = 'Main Category'
    parameter_name = 'main_category'

    def lookups(self, request, model_admin):
        # Only categories where parent is None
        return [(cat.id, cat.category_name) for cat in Category.objects.filter(parent__isnull=True)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(browse_page__category__id=self.value())
        return queryset
    
class CategoryBrowseSectionAdmin(SortableAdminMixin,admin.ModelAdmin):
    list_display = ['title', 'get_category_name', 'section_type', 'browse_page', 'order']
    list_filter = [MainCategoryFilter, 'section_type', 'browse_page']
    ordering = ['order']
    def get_category_name(self, obj):
        return obj.browse_page.category.category_name
    get_category_name.short_description = 'Category'
    get_category_name.admin_order_field = 'browse_page__category__name'

    def get_inline_instances(self, request, obj=None):
        inline_instances = []

        section_type = None
        if obj:
            section_type = obj.section_type
        elif request.method == 'POST':
            section_type = request.POST.get('section_type')
        elif request.method == 'GET':
            section_type = request.GET.get('section_type')

        if section_type == 'product_slider':
            inline_classes = [ProductAssignmentInline]
        elif section_type == 'subcategory_slider':
            inline_classes = [SubCategoryAssignmentInline]
        else:
            inline_classes = []

        for inline_class in inline_classes:
            inline = inline_class(self.model, self.admin_site)
            inline_instances.append(inline)

        return inline_instances


class CategoryBrowseSectionInline(SortableInlineAdminMixin,admin.StackedInline):
    model = CategoryBrowseSection
    extra = 1
    show_change_link = True



class CategoryBrowsePageAdmin(SortableAdminMixin,admin.ModelAdmin):
    form = CategoryBrowsePageForm
    list_display = ['category','order']
    inlines = [CategoryBrowseSectionInline]


class ProductAssignmentAdmin(SortableAdminMixin,admin.ModelAdmin):
    list_display = ['section', 'order']
    ordering = ['order']


class SubCategoryAssignmentAdmin(admin.ModelAdmin):
    list_display = ['section', 'product', 'order']



admin.site.register(Category, CategoryAdmin)
admin.site.register(UnifieldProduct, UnifieldProductAdmin)
admin.site.register(ProductGallery)
admin.site.register(MediaUpload, MediaUploadAdmin)
admin.site.register(CategoryBrowsePage, CategoryBrowsePageAdmin)
admin.site.register(CategoryBrowseSection, CategoryBrowseSectionAdmin)
admin.site.register(ProductAssignment, ProductAssignmentAdmin)
admin.site.register(SubCategoryAssignment)
admin.site.register(ProductCloneTable)