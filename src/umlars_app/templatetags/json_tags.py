import json

from django import template


register = template.Library()


@register.inclusion_tag("partials/recursive_json.html")
def render_json(data):
    """
    Renders nested JSON data recursively.
    """
    return {"data": data}


@register.filter
def pretty_json(value):
    return json.dumps(value, indent=4)
