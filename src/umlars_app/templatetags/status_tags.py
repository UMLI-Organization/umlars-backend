from django import template

register = template.Library()


@register.inclusion_tag("partials/enum_status.html")
def render_status(enum_object, enum_class, status_text = None, additional_classes_string="fs-6"):
    status_text = status_text or enum_class(enum_object).name
    return {"enum_object": enum_object, "enum_class": enum_class, "additional_classes_string": additional_classes_string, "status_text": status_text}
