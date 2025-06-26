from dal import autocomplete

class CustomProductAutocomplete(autocomplete.ModelSelect2Multiple):
    # Override build_attrs to inject object_id from the URL (admin edit page)
    def build_attrs(self, base_attrs, extra_attrs=None, **kwargs):
        attrs = super().build_attrs(base_attrs, extra_attrs, **kwargs)
        attrs['data-autocomplete-object-id'] = ''  # placeholder, will be filled by JS
        return attrs