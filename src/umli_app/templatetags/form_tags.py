from django import template

register = template.Library()


@register.inclusion_tag("partials/formatted_form.html")
def render_form_with_errors(form):
    """
    Formats a form with errors using bootstrap.
    """
    return {"form": form}


@register.inclusion_tag("partials/file_upload_form.html")
def render_file_upload_form(form):
    """
    Formats a form with errors using bootstrap.
    """
    return {"form": form}
