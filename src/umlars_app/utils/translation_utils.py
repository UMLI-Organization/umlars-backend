from typing import Iterator, Optional

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.contrib import messages

from umlars_app.message_broker.producer import send_uploaded_model_message, create_message_data
from umlars_app.models import UmlModel, ProcessStatus


def schedule_translate_uml_model(request: HttpRequest, model: UmlModel, ids_of_source_files: Optional[Iterator[int]] = None, ids_of_edited_files: Optional[Iterator[int]] = None, ids_of_new_submitted_files: Optional[Iterator[int]] = None, ids_of_deleted_files: Optional[Iterator[int]] = None, reset_files_status: bool = False) -> HttpResponse:
    try:
        message_data = create_message_data(model, ids_of_source_files, ids_of_edited_files, ids_of_new_submitted_files, ids_of_deleted_files)
        send_uploaded_model_message(
            message_data=message_data,
        )
        if reset_files_status:
            for file in model.source_files.all():
                file.state = ProcessStatus.QUEUED
                file.save()

    except Exception as ex:
        error_message = f"Connection with the translation service cannot be established: {ex}"
        messages.warning(request, error_message)
        return redirect("home")
