from django import template

register = template.Library()

@register.filter
def get_item(list_obj, index):
    try:
        return list_obj[index]
    except (IndexError, TypeError):
        return ''