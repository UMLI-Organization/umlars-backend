from django import template

register = template.Library()   


@register.filter(name='zip')
def zip_lists(list_1: list, list_2: list) -> list:
    return zip(list_1, list_2)


@register.filter(name='dir_tag')
def dir_tag(obj):
  return dir(obj)


@register.filter(name='getattr_tag')
def getattr_tag(obj, attr):
    return getattr(obj, attr, None)