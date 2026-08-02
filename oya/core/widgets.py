"""
Shared form widgets for OYA.

AutocompleteSelectWidget is the ONE component every form in the project
should use whenever it needs to let a user pick a Member or a User
(login account) — yearly dues, project/general donations, pledges,
donation-group assignment, outside-donor referrals, etc.

It replaces a plain <select> with a text input that performs live AJAX
search (debounced, server-side, paginated by the endpoint's own [:15]
slice) instead of preloading every record into the page. The endpoints
it talks to are members.views.member_autocomplete_search and
accounts.views.user_search_ajax — both return the same JSON shape, so
this one widget/JS pair drives both without special-casing.

Usage in a ModelForm:

    class DonationForm(forms.ModelForm):
        class Meta:
            model = Donation
            fields = [..., "member", ...]
            widgets = {
                "member": AutocompleteSelectWidget(
                    search_url_name="members:member_autocomplete_search",
                    placeholder="Search member by name, no. or phone…",
                ),
                ...
            }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # lets the widget resolve the display text for an existing value
            self.fields["member"].widget.display_queryset = Member.objects.all()
"""
from django import forms
from django.urls import reverse


class AutocompleteSelectWidget(forms.Widget):
    """Drop-in replacement for forms.Select on a ForeignKey field."""

    template_name = "widgets/autocomplete_select.html"
    input_type = "hidden"

    def __init__(self, search_url_name, attrs=None, placeholder="Search…",
                 allow_clear=True, min_chars=1):
        self.search_url_name = search_url_name
        self.placeholder = placeholder
        self.allow_clear = allow_clear
        self.min_chars = min_chars
        # Set by the owning form's __init__ so the widget can resolve the
        # human-readable label for a pre-filled value (edit forms).
        self.display_queryset = None
        super().__init__(attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        widget = context["widget"]
        widget["search_url"] = reverse(self.search_url_name)
        widget["placeholder"] = self.placeholder
        widget["allow_clear"] = self.allow_clear
        widget["min_chars"] = self.min_chars
        widget["display_value"] = self._resolve_display(value)
        field_id = widget.get("attrs", {}).get("id")
        widget["search_input_id"] = f"{field_id}_search" if field_id else ""
        return widget

    def id_for_label(self, id_):
        # <label for=...> should focus the visible search box, not the
        # hidden input that carries the real FK value (id_<field> is kept
        # on the hidden input so existing JS that reads/writes it by that
        # canonical id — e.g. donation_form.html's invited_by auto-fill —
        # keeps working unchanged).
        return f"{id_}_search" if id_ else id_

    def _resolve_display(self, value):
        if not value or self.display_queryset is None:
            return ""
        try:
            return str(self.display_queryset.get(pk=value))
        except Exception:
            return ""

    def value_from_datadict(self, data, files, name):
        val = data.get(name)
        return val or None

    def value_omitted_from_data(self, data, files, name):
        return name not in data
