from django import forms


class BootstrapFormMixin:
    """Adds Bootstrap 3 `form-control` to every non-radio/checkbox widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.RadioSelect, forms.CheckboxInput)):
                continue
            css = widget.attrs.get("class", "")
            widget.attrs["class"] = (css + " form-control").strip()
