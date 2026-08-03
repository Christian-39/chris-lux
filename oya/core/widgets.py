import logging
from django import forms
from django.urls import reverse, NoReverseMatch

logger = logging.getLogger("oya")


class AutocompleteSelectWidget(forms.Widget):
    """
    Reusable searchable-select used everywhere a form needs to pick a
    Member or User (yearly dues, project/general donations, pledges,
    donation-group assignment, outside-donor referrals, etc). Renders a
    text input that performs live AJAX search, plus a hidden input that
    carries the real submitted value.

    IMPORTANT — id handling: the hidden input renders at the CANONICAL
    "id_<field>" (e.g. id_member), matching what a plain <select> would
    have gotten. Several pages have JS that reads/writes that field by
    id directly (e.g. dues_form.html, income_form.html auto-fill and
    validation) — losing this id makes those scripts throw on a null
    element, which is what broke the member fields project-wide. The
    visible search box gets "id_<field>_search" instead, and
    id_for_label() is overridden so <label for=...> focuses that visible
    box rather than the hidden one.
    """
    template_name = "widgets/autocomplete_select.html"

    def __init__(self, search_url_name=None, placeholder=None, min_chars=1,
                 allow_clear=True, attrs=None):
        self.search_url_name = search_url_name
        self.placeholder = placeholder or "Search…"
        self.min_chars = min_chars
        self.allow_clear = allow_clear
        self.display_queryset = None  # Populated by the form's __init__
        super().__init__(attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        widget = context["widget"]

        # Resolve the AJAX endpoint URL
        search_url = ""
        if not self.search_url_name:
            logger.warning(
                "AutocompleteSelectWidget for field '%s' has no search_url_name set — "
                "the search box will render but searching will not work.",
                name,
            )
        else:
            try:
                search_url = reverse(self.search_url_name)
            except NoReverseMatch:
                logger.error(
                    "AutocompleteSelectWidget for field '%s': search_url_name=%r "
                    "did not resolve via reverse(). Check that this URL name exists "
                    "and is namespaced correctly (app_name + include()).",
                    name, self.search_url_name,
                )
                search_url = ""
        widget["search_url"] = search_url
        widget["placeholder"] = self.placeholder
        widget["min_chars"] = self.min_chars
        widget["allow_clear"] = self.allow_clear

        # The canonical id (e.g. id_member) goes on the hidden input, for
        # compatibility with existing page JS that reads this field by id.
        field_id = widget.get("attrs", {}).get("id")
        widget["search_input_id"] = f"{field_id}_search" if field_id else ""

        # Pre-fill the visible input with the selected record's name (edit mode)
        display_text = ""
        if value and self.display_queryset is not None:
            try:
                obj = self.display_queryset.get(pk=value)
                display_text = getattr(obj, "full_name", str(obj))
            except Exception:
                display_text = ""
        widget["display_text"] = display_text

        return widget

    def id_for_label(self, id_):
        # <label for=...> should focus the visible search box, not the
        # hidden input that carries the real value.
        return f"{id_}_search" if id_ else id_

    def value_from_datadict(self, data, files, name):
        value = data.get(name)
        return value or None

    def value_omitted_from_data(self, data, files, name):
        return name not in data
