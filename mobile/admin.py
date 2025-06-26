from django.contrib import admin
from .models import Event, EventAds
from django.forms.models import BaseInlineFormSet, inlineformset_factory
from django.core.exceptions import ValidationError
from django import forms
from django.utils.html import format_html



class EventAdsInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        total_forms = len([form for form in self.forms if not form.cleaned_data.get('DELETE', False)])
        if total_forms > 6:
            raise ValidationError("You can only add up to 6 ads for each event.")
        

class EventAdsInline(admin.TabularInline):  # or admin.StackedInline
    model = EventAds
    extra = 0
    max_num = 6
    formset = EventAdsInlineFormSet


class EventAdminForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = '__all__'
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }



class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'active', 'default', 'color_swatch')
    list_editable = ('active', 'default')
    list_filter = ('active', 'default')
    search_fields = ('title',)
    ordering = ('-start_date',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [EventAdsInline]

    def save_model(self, request, obj, form, change):
        if obj.default:
            Event.objects.exclude(pk=obj.pk).update(default=False)
        super().save_model(request, obj, form, change)

    def color_swatch(self, obj):
        return format_html('<div style="width: 30px; height: 15px; background: {};"></div>', obj.home_color)
    color_swatch.short_description = 'Color'


admin.site.register(Event, EventAdmin)
admin.site.register(EventAds)
