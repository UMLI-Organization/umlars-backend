from django import template

register = template.Library()

@register.inclusion_tag('recursive_json.html')
def render_json(data):
    """
    Renders nested JSON data recursively.
    """
    return {'data': data}
