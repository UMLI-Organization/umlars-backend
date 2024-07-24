from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.contrib import messages

from umlars_app.message_broker.producer import send_uploaded_model_message, create_message_data
from umlars_app.models import UmlModel


def schedule_translate_uml_model(request: HttpRequest, model: UmlModel) -> HttpResponse:
    try:
        message_data = create_message_data(model)
        send_uploaded_model_message(
            message_data=message_data,
        )
    except Exception as ex:
        error_message = f"Connection with the translation service cannot be established: {ex}"
        messages.warning(request, error_message)
        return redirect("home")
