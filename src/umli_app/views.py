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
from umli_app.forms import SignUpForm, AddUmlModelForm, AddUmlFileFormset, EditUmlFileFormset, FilesGroupingForm, ExtensionsGroupingFormSet, RegexGroupingFormSet, ExtensionsGroupingRuleForm, RegexGroupingRuleForm
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



def update_uml_model(request: HttpRequest, pk: int) -> HttpResponse:
    SOURCE_FILES_FORMSET_PREFIX = "source_files"
    if request.user.is_authenticated:
        uml_model_to_update = UmlModel.objects.prefetch_related("source_files").get(id=pk)
        if request.method == "POST":
            
            form = AddUmlModelForm(request.POST, instance=uml_model_to_update)
            formset = EditUmlFileFormset(request.POST, request.FILES, prefix=SOURCE_FILES_FORMSET_PREFIX, instance=uml_model_to_update)

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
                        return render(request, "update-uml-model.html", {"form": form, "formset": formset})
            else:
                logger.error(f"UML model: {form.errors} could not be added.")
                messages.error(request, "UML model could not be added.")
                return render(request, "update-uml-model.html", {"form": form, "formset": formset})
            
        else:
            form = AddUmlModelForm(instance=uml_model_to_update)
            formset = EditUmlFileFormset(prefix=SOURCE_FILES_FORMSET_PREFIX, instance=uml_model_to_update)
            return render(request, "update-uml-model.html", {"form": form, "formset": formset})

    else:
        messages.warning(request, "You need to be logged in to update this UML model")
        return redirect("home")

def bulk_upload_uml_models(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:

        if request.method == "POST":
            files_form = FilesGroupingForm(request.POST, request.FILES)
            extension_group_formset = ExtensionsGroupingFormSet(request.POST, prefix='extensions')
            regex_group_formset = RegexGroupingFormSet(request.POST, prefix='regex')


            if files_form.is_valid() and extension_group_formset.is_valid() and regex_group_formset.is_valid():
                ...
                for file in files_form.files:
                    ...

            else:
                # Re-render the form with errors
                return render(request, 'bulk-upload-uml-models.html', {
                    'form': files_form,
                    'extension_group_formset': extension_group_formset,
                    'regex_group_formset': regex_group_formset,
                })
        else:
            files_form = FilesGroupingForm()
            extension_group_formset = ExtensionsGroupingFormSet(prefix='extensions')
            regex_group_formset = RegexGroupingFormSet(prefix='regex')

        return render(request, 'bulk-upload-uml-models.html', {
            'form': files_form,
            'extension_group_formset': extension_group_formset,
            'regex_group_formset': regex_group_formset,
        })

    else:
        messages.warning(request, "You need to be logged in to upload files.")
        return redirect("home")


def process_files(files, join_extensions, regex_pattern):
    # Logic to process files and split them according to the rules.
    detected_models = []
    # Implement the logic to group files based on the provided rules
    # This is a placeholder implementation
    for file in files:
        model_name = determine_model_name(file, join_extensions, regex_pattern)
        model = UmlModel(name=model_name, description="")
        model.save()
        UmlFile(model=model, filename=file.name, data=file.read().decode('utf-8'), format=determine_format(file.name)).save()
        detected_models.append(model)
    return detected_models

def determine_model_name(file, join_extensions, regex_pattern):
    # Logic to determine model name based on file and rules
    return file.name.split('.')[0]

def determine_format(filename):
    # Logic to determine format based on filename extension
    return filename.split('.')[-1]

def save_detected_models(detected_models):
    for model in detected_models:
        model.save()
        for file in model.files.all():
            file.save()