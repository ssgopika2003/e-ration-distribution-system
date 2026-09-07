from django import template

register = template.Library()


@register.filter(name='get_item')
def get_item(dictionary, key):
    """Return dictionary[key] if present, else an empty string.

    Works with Django template filter lookups like: {{ mydict|get_item:key }}
    """
    try:
        return dictionary.get(key, '')
    except Exception:
        # dictionary might not be a dict (e.g., QuerySet); fallback to attribute access
        try:
            return getattr(dictionary, str(key), '')
        except Exception:
            return ''
