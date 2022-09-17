from django import template

register = template.Library()


@register.filter(name="zip")
def zip_lists(value, arg):
    if arg:
        return zip(value, arg)
    else:
        empty = [None] * len(value)
        return zip(value, empty)
