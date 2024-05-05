from django import template

register = template.Library()


@register.inclusion_tag("formatted_form.html")
def render_form_with_errors(form):
    """
    Formats a form with errors using bootstrap.
    """
    return {"form": form}
