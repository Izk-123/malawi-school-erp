"""Shared form helpers."""
from django import forms


def enable_dropzone(form):
    """
    Call from a ModelForm's __init__ to progressively enhance every
    FileField/ImageField on the form with the drag-and-drop widget
    (static/js/dropzone.js) - one line instead of hand-editing every
    form's widgets dict. Also passes along the existing filename when
    editing a record that already has a file, so the widget can show
    'current file: ...' instead of an empty drop zone.
    """
    for name, field in form.fields.items():
        if isinstance(field, forms.ImageField) or isinstance(field, forms.FileField):
            existing_classes = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing_classes + ' dropzone-input').strip()
            if field.widget.attrs.get('accept') is None and isinstance(field, forms.ImageField):
                field.widget.attrs['accept'] = 'image/*'
            current_value = form.initial.get(name) or getattr(form.instance, name, None)
            if current_value:
                try:
                    field.widget.attrs['data-existing-filename'] = current_value.name.rsplit('/', 1)[-1]
                except (AttributeError, ValueError):
                    pass
