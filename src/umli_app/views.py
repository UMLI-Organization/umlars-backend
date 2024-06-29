import logging
from typing import List, Set, NamedTuple, Dict
import re
from collections import defaultdict

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
from umli_app.utils.files_utils import decode_file
from umli_app.exceptions import UnsupportedFileError


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
                files = request.FILES.getlist('files')

                # Process the extension grouping rules
                extension_rules: List[Set[str]] = []
                for form in extension_group_formset:
                    extensions = form.cleaned_data.get('extensions')
                    if extensions:
                        extension_rules.append(set(ext.strip('. ') for ext in extensions.split(',')))

                # Process the regex grouping rules
                regex_rules: List[str] = []
                for form in regex_group_formset:
                    regex_pattern = form.cleaned_data.get('regex_pattern')
                    if regex_pattern:
                        regex_rules.append(regex_pattern)

                detected_models = process_files(files, extension_rules, regex_rules)
                
                if files_form.cleaned_data['dry_run']:
                    model_forms = list()
                    file_formsets = list()

                    for i, model in enumerate(detected_models):
                        model_forms.append(AddUmlModelForm(instance=model))
                        file_formsets.append(EditUmlFileFormset(instance=model, prefix=f'source_files_{i}'))


                    return render(request, 'review-bulk-upload.html', {
                        'model_forms': zip(model_forms, file_formsets),
                        'empty_file_form': AddUmlFileFormset().empty_form,
                    })

                else:
                    save_detected_models(detected_models)
                    messages.success(request, "Files uploaded successfully.")
                    return redirect('home')

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


def process_files(
    files: List[UploadedFile], 
    extension_groups: List[List[str]], 
    regex_patterns: List[str]
) -> List[UmlModel]:
    """
    Process files according to the provided grouping rules.

    Args:
        files (List[UploadedFile]): List of uploaded files.
        extension_groups (List[List[str]]): List of extension groups for grouping files.
        regex_patterns (List[str]): List of regex patterns for grouping files.

    Returns:
        List[UmlModel]: List of UmlModel instances created from the files.
    """
    detected_models = []
    grouped_files = group_files(files, extension_groups, regex_patterns)
    logger.info(f"Grouped files: {grouped_files}")

    for group in grouped_files:
        model_name = determine_model_name(group)
        
        model = UmlModel.objects.create(name=model_name, description=f"Created from bulk load of files.")
        
        for file in group.files:
            try:
                UmlFile.objects.create(
                    model=model,
                    filename=file.name,
                    data=decode_file(file),
                    format=UmlFile.SupportedFormat.UNKNOWN
                )
            except UnsupportedFileError as ex:
                logger.error(f"Error processing file: {file.name}.\nError: {ex}")
                continue

        detected_models.append(model)
    
    return detected_models



class ModelFilesGroup(NamedTuple):
    model_name: str | None = None
    files: List[UploadedFile] = []



def create_filenames_to_extensions_mapping(files: List[UploadedFile]) -> Dict[str, Dict[str, List[UploadedFile]]]:
    """
    Create a mapping from filenames to extensions.

    Args:
        files (List[UploadedFile]): List of uploaded files.

    Returns:
        Dict[str, Dict[str, List[UploadedFile]]]: Mapping from filenames to extensions.
    """
    filenames_mapping = defaultdict(lambda: defaultdict(list))
    for file in files:
        base_name, extension = file.name.rsplit('.', 1)
        filenames_mapping[base_name][extension].append(file)

    return filenames_mapping


def group_files(
    files: List[UploadedFile], 
    extension_groups: List[List[str]], 
    regex_patterns: List[str]
) -> List[ModelFilesGroup]:
    """
    Group files according to extension groups and regex patterns.

    Args:
        files (List[UploadedFile]): List of uploaded files.
        extension_groups (List[List[str]]): List of extension groups for grouping files.
        regex_patterns (List[str]): List of regex patterns for grouping files.

    Returns:
        List[ModelFilesGroup]: List of grouped files.
    """
    grouped_files: List[ModelFilesGroup] = []

    if not extension_groups and not regex_patterns:
        # If no grouping rules provided, treat each file as a separate group
        for file in files:
            grouped_files.append(ModelFilesGroup(model_name=determine_model_name_from_file(file), files=[file]))
        return grouped_files
    
    filenames_to_extensions_mapping = create_filenames_to_extensions_mapping(files)

    # Group by extension
    for extensions in extension_groups:
        for base_name, extensions_group in list(filenames_to_extensions_mapping.items()):
            group = ModelFilesGroup()
            for extension in extensions:
                files = extensions_group.pop(extension, [])
                group.files.extend(files)

            if group.files:
                grouped_files.append(group)
                if not extensions_group:  # If no extensions left for this base name, remove the entry
                    del filenames_to_extensions_mapping[base_name]

    # Group by regex patterns
    for pattern in regex_patterns:
        regex = re.compile(pattern)
        regex_groups = defaultdict(list)
        for base_name, extensions_group in list(filenames_to_extensions_mapping.items()):
            for extension, files in list(extensions_group.items()):
                for file in files:
                    match = regex.match(file.name)
                    if match:
                        regex_key = match.group(0)
                        regex_groups[regex_key].append(file)
                # Remove processed extensions
                del extensions_group[extension]
            if not extensions_group:  # If no extensions left for this base name, remove the entry
                del filenames_to_extensions_mapping[base_name]

        for regex_key, files in regex_groups.items():
            grouped_files.append(ModelFilesGroup(model_name=regex_key, files=files))

    # Any remaining files are treated as separate groups containing one file each
    for base_name, extensions_group in filenames_to_extensions_mapping.items():
        for extension, files in extensions_group.items():
            for file in files:
                grouped_files.append(ModelFilesGroup(model_name=determine_model_name_from_file(file), files=[file]))

    return grouped_files



def determine_model_name(group: ModelFilesGroup) -> str:
    """
    Determine the name for the UML model based on the grouped files.

    Args:
        group (ModelFilesGroup): Group of files.

    Returns:
        str: The determined model name.
    """
    return determine_model_name_from_file(group.files[0]) if group.model_name is None else group.model_name or "Unnamed Model"


def determine_model_name_from_file(file: UploadedFile) -> str:
    """
    Determine the name for the UML model based on the grouped files.

    Args:
        group (ModelFilesGroup): Group of files.

    Returns:
        str: The determined model name.
    """
    return file.name.rsplit('.', 1)[0] or "Unnamed Model"


def save_detected_models(detected_models: List[UmlModel]) -> None:
    """
    Save the detected UML models to the database.

    Args:
        detected_models (List[UmlModel]): List of UmlModel instances.
    """
    for model in detected_models:
        model.save()
        for file in model.files:
            file.save()