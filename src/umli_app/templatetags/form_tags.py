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
    Formats a form for file upload or edit.
    """
    return {"form": form}


@register.inclusion_tag("partials/model_upload_form.html")
def render_model_upload_form(form, formset):
    """
    Formats a form for model upload or edit.
    """
    return {"form": form, "formset": formset}


@register.inclusion_tag("partials/model_upload_form_fields.html")
def render_model_upload_form_fields(form, formset):
    """
    Formats a form for model upload or edit.
    """
    return {"form": form, "formset": formset}
