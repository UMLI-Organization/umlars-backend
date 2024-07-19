from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.contrib import messages
import pika

from umli_app.message_broker.producer import send_uploaded_file_message, create_message_data



def translate_uml_model(request: HttpRequest, model_pk: int) -> HttpResponse:
    if request.user.is_authenticated:
        try:
            # TODO: inject with dependency injection
            # TODO: take from env
            connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
            channel = connection.channel()

            send_uploaded_file_message(
                channel,
                create_message_data(
                    id=model_pk,
                )
            )
        except Exception as ex:
            error_message = f"Connection with the translation service cannot be established: {ex}"
            messages.warning(request, error_message)
            return redirect("home")
