import logging
from typing import Dict

import pika
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest
from django.core.files.uploadedfile import UploadedFile
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import transaction

from umli_app.message_broker.producer import send_uploaded_file_message, create_message_data
from umli_app.models import UmlModel, UmlFile
from umli_app.forms import SignUpForm, AddUmlModelForm, AddUmlFileFormset
from umli_backend.settings import LOGGING


main_logger_name = next(iter(LOGGING['loggers'].keys()))
logger = logging.getLogger(main_logger_name).getChild(__name__)


def home(request: HttpRequest) -> HttpResponse:

    if request.method == "POST":
        return login_user(request)
    else:
        uml_models = UmlModel.objects.prefetch_related("metadata", "source_files").all()
        return render(request, "home.html", {"uml_models": uml_models})


def login_user(request: HttpRequest) -> HttpResponse:
    username = request.POST.get("username")
    password = request.POST.get("password")
    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)
        messages.success(request, f"Welcome {username}")
        return redirect("home")
    else:
        messages.warning(request, "Invalid credentials")
        return redirect("home")


def logout_user(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.success(request, "You have been logged out")
    return redirect("home")


def register_user(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()

            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password1")
            user = authenticate(request, username=username, password=password)
            login(request, user)

            messages.success(request, "You have successfully registered")
            return redirect("home")
    else:
        form = SignUpForm()

    return render(request, "register.html", {"form": form})


def uml_model(request: HttpRequest, pk: int) -> HttpResponse:
    if request.user.is_authenticated:
        uml_model = UmlModel.objects.prefetch_related("metadata").get(id=pk)

        # Read and decode the file content
        # TODO: redo after final file format decision
        try:
            xml_content = uml_model.source_file.read().decode("utf-8")

            import xml.dom.minidom as minidom

            # Pretty-print the XML content
            pretty_xml = minidom.parseString(xml_content).toprettyxml(indent="  ")
        except ValueError:
            pretty_xml = uml_model.formatted_data

        return render(
            request,
            "uml-model.html",
            {"uml_model": uml_model, "pretty_xml": pretty_xml},
        )
    else:
        messages.warning(request, "You need to be logged in to view this page")
        return redirect("home")


def delete_uml_model(request: HttpRequest, pk: int) -> HttpResponse:
    if request.user.is_authenticated:
        uml_model_to_delete = UmlModel.objects.get(id=pk)
        uml_model_to_delete.delete()
        messages.success(request, "UML model has been deleted.")
        return redirect("home")
    else:
        messages.warning(request, "You need to be logged in to delete this UML model")
        return redirect("home")


def translate_uml_model(request: HttpRequest, pk: int) -> HttpResponse:
    if request.user.is_authenticated:
        try:
            # TODO: inject with dependency injection
            # TODO: take from env
            connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
            channel = connection.channel()

            send_uploaded_file_message(
                channel,
                create_message_data(
                    id=pk,
                )
            )
        except Exception as ex:
            error_message = f"Connection with the translation service cannot be established: {ex}"
            messages.warning(request, error_message)
            return redirect("home")


def add_uml_model(request: HttpRequest) -> HttpResponse:
    SOURCE_FILES_FORMSET_PREFIX = "source_files"
    if request.user.is_authenticated:
        if request.method == "POST":
            form = AddUmlModelForm(request.POST)
            formset = AddUmlFileFormset(request.POST, request.FILES, prefix=SOURCE_FILES_FORMSET_PREFIX)

            if form.is_valid():
                with transaction.atomic():
                    added_uml_model = form.save()
                    formset.instance = added_uml_model
                    if formset.is_valid():
                        added_uml_files = formset.save()
                        logger.info(f"UML files: {added_uml_files} have been added.")
                        # TODO: add translate for each file
                        messages.success(request, f"UML model: {added_uml_model} has been added.")
                        logger.info(f"UML model: {added_uml_model} has been added.")
                        return redirect("home")
                    else:
                        logger.error(f"UML files: {formset.errors} could not be added.")
                        messages.error(request, "UML files could not be added.")
                        return render(request, "add-uml-model.html", {"form": form, "formset": formset})
            else:
                logger.error(f"UML model: {form.errors} could not be added.")
                messages.error(request, "UML model could not be added.")
                return render(request, "add-uml-model.html", {"form": form, "formset": formset})
            
        else:
            form = AddUmlModelForm()
            formset = AddUmlFileFormset(prefix=SOURCE_FILES_FORMSET_PREFIX)

        return render(request, "add-uml-model.html", {"form": form, "formset": formset})

    return redirect("home")


# TODO: do zmiany
def update_uml_files(files: Dict[str, UploadedFile], associated_model: UmlModel, format: str) -> HttpResponse:
    for file_name, file in files.items():
        UmlFile.objects.create(
            file=file.read(),
            format=format,
            filename = file_name,
            model=associated_model
        )

    return HttpResponse("Files have been updated.")


# TODO: prefetch files and use formset
def update_uml_model(request: HttpRequest, pk: int) -> HttpResponse:
    if request.user.is_authenticated:
        uml_model_to_update = UmlModel.objects.get(id=pk)
        form = AddUmlModelForm(request.POST or None, request.FILES or None, instance=uml_model_to_update)
        if form.is_valid():
            updated_model = form.save()
            update_uml_files(form.cleaned_data["source_files"], form.cleaned_data["format"], updated_model)

            translate_uml_model(request, updated_model.id)

            messages.success(request, "UML model has been updated.")
            return redirect("home")
        return render(request, "update-uml-model.html", {"form": form})
    else:
        messages.warning(request, "You need to be logged in to update this UML model")
        return redirect("home")


def bulk_upload_uml_models(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("home")
    else:
        messages.warning(request, "You need to be logged in to update this UML model")
        return redirect("home")

