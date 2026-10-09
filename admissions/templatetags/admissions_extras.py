"""Custom template filters used by admissions partials."""
from django import template

register = template.Library()


@register.filter
def split(value, sep=','):
    """Split a string into a list. Usage: {{ "a:b:c"|split:":" }}"""
    if value is None or value == '':
        return []
    return str(value).split(sep)


@register.filter
def at(seq, index):
    """Safely return seq[index]. Usage: {{ my_list|at:0 }}"""
    try:
        return seq[int(index)]
    except (IndexError, ValueError, TypeError, KeyError):
        return ''