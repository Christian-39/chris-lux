from django import forms
from django.urls import reverse
from django.utils.safestring import mark_safe


class AutocompleteSelectWidget(forms.Widget):
    """
    Renders a search-as-you-type select backed by the OYA Autocomplete JS.
    """
    template_name = "widgets/autocomplete_select.html"

    def __init__(self, search_url_name=None, placeholder=None, min_chars=1, **kwargs):
        self.search_url_name = search_url_name
        self.placeholder = placeholder or "Search…"
        self.min_chars = min_chars
        self.display_queryset = None  # Populated by the form's __init__
        super().__init__(**kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        # Resolve the AJAX endpoint URL
        search_url = ""
        if self.search_url_name:
            try:
                search_url = reverse(self.search_url_name)
            except Exception:
                pass
        context["widget"]["search_url"] = search_url
        context["widget"]["placeholder"] = self.placeholder
        context["widget"]["min_chars"] = self.min_chars

        # Pre-fill the visible input with the selected member's name (edit mode)
        display_text = ""
        if value and self.display_queryset is not None:
            try:
                obj = self.display_queryset.get(pk=value)
                display_text = getattr(obj, "full_name", str(obj))
            except Exception:
                pass
        context["widget"]["display_text"] = display_text

        return context