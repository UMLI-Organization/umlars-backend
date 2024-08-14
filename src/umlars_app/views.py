from typing import Deque, Set, Iterator, Tuple
from collections import deque

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import transaction
from django.forms.models import model_to_dict
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from umlars_app.utils.translation_utils import schedule_translate_uml_model
from umlars_app.models import UmlModel, UmlFile
from umlars_app.forms import SignUpForm, EditUserForm, AddUmlModelForm,UpdateUmlModelForm, AddUmlFileFormset, EditUmlFileFormset, FilesGroupingForm, ExtensionsGroupingFormSet, RegexGroupingFormSet, AddUmlModelFormset, ChangePasswordForm
from umlars_app.utils.files_utils import decode_file
from umlars_app.utils.grouping_utils import group_files, determine_model_name
from umlars_app.exceptions import UnsupportedFileError
import umlars_app.settings
from umlars_app.utils.logging import get_new_sublogger

logger = get_new_sublogger(__name__)


def home(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        return login_user(request)
    else:
        searched_model_name = request.GET.get('model_name')
        if searched_model_name is not None:
            uml_models = UmlModel.objects.prefetch_related("source_files").filter(name__icontains=searched_model_name, accessed_by__id=request.user.id).order_by("id")
        else:
            uml_models = UmlModel.objects.prefetch_related("source_files").filter(accessed_by__id=request.user.id).all().order_by("id")

        # Pagination
        paginator = Paginator(uml_models, 10)  # Show 10 models per page
        page = request.GET.get('page')
        try:
            uml_models = paginator.page(page)
        except PageNotAnInteger:
            uml_models = paginator.page(1)
        except EmptyPage:
            uml_models = paginator.page(paginator.num_pages)

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


def delete_current_user(request: HttpRequest) -> HttpResponse:
    user = request.user
    if user.is_authenticated:
        user.delete()
        messages.success(request, "User has been deleted.")
        return redirect("home")
    else:
        messages.warning(request, "You need to be logged in to delete the user...")
        return redirect("home")


def profile(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = EditUserForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, "Profile has been updated.")
                return redirect("home")
            else:
                return render(request, "profile.html", {"form": form})
        else:
            form = EditUserForm(instance=request.user)
            return render(request, "profile.html", {"form": form})
    
    else:
        messages.warning(request, "You need to be logged in to view this page")
        return redirect("home")


def uml_model(request: HttpRequest, pk: int) -> HttpResponse:
    if request.user.is_authenticated:
        uml_model = UmlModel.objects.prefetch_related("source_files").filter(accessed_by__id=request.user.id).get(id=pk)

        # Read and decode the file content
        # TODO: redo after final file format decision
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
        try:
            uml_model_to_delete = UmlModel.objects.filter(accessed_by__id=request.user.id).get(id=pk)
        except UmlModel.DoesNotExist:
            messages.warning(request, "UML model already does not exist")
            return redirect("home")
        uml_model_to_delete.delete()
        messages.success(request, "UML model has been deleted.")
        return redirect("home")
    else:
        messages.warning(request, "You need to be logged in to delete this UML model")
        return redirect("home")



def add_uml_model(request: HttpRequest) -> HttpResponse:
    SOURCE_FILES_FORMSET_PREFIX = "source_files"
    if request.user.is_authenticated:
        if request.method == "POST":
            form = AddUmlModelForm(request.POST, user=request.user)
            formset = AddUmlFileFormset(request.POST, request.FILES, prefix=SOURCE_FILES_FORMSET_PREFIX)

            if form.is_valid():
                with transaction.atomic():
                    added_uml_model = form.save()
                    formset.instance = added_uml_model
                    if formset.is_valid():
                        added_uml_files = formset.save()
                        logger.info(f"UML files: {added_uml_files} have been added.")
                        
                        source_files_ids = set(added_uml_model.source_files.values_list("id", flat=True))

                        schedule_translate_uml_model(request, added_uml_model, source_files_ids, ids_of_new_submitted_files=source_files_ids)
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
            form = AddUmlModelForm(user=request.user)
            formset = AddUmlFileFormset(prefix=SOURCE_FILES_FORMSET_PREFIX)
            return render(request, "add-uml-model.html", {"form": form, "formset": formset})

    return redirect("home")


def _calculate_files_changes(source_files_ids_before_edit: Set[int], source_files_ids_after_edit: Set[int], updated_uml_files: Iterator[UmlFile]) -> Tuple[Set[int], Set[int], Set[int]]:
    deleted_files_ids = source_files_ids_before_edit - source_files_ids_after_edit
    new_submitted_files_ids = source_files_ids_after_edit - source_files_ids_before_edit
    new_or_edited_files_ids = set(file.id for file in updated_uml_files)
    updated_files_ids = new_or_edited_files_ids & source_files_ids_before_edit
    return deleted_files_ids, updated_files_ids, new_submitted_files_ids


def update_uml_model(request: HttpRequest, pk: int) -> HttpResponse:
    SOURCE_FILES_FORMSET_PREFIX = "source_files"
    if request.user.is_authenticated:
        uml_model_to_update = UmlModel.objects.prefetch_related("source_files").filter(accessed_by__id=request.user.id).get(id=pk)
        if request.method == "POST":
            form = UpdateUmlModelForm(request.POST, instance=uml_model_to_update)
            formset = EditUmlFileFormset(request.POST, request.FILES, prefix=SOURCE_FILES_FORMSET_PREFIX, instance=uml_model_to_update)

            if form.is_valid():
                with transaction.atomic():
                    added_uml_model = form.save()
                    formset.instance = added_uml_model
                    if formset.is_valid():
                        # Get initial file IDs before editing
                        source_files_ids_before_edit = set(uml_model_to_update.source_files.values_list("id", flat=True))

                        # Save formset to update the files
                        updated_uml_files = formset.save()

                        
                        if formset.has_changed():
                            # Get updated file IDs from the database
                            source_files_ids_after_edit = set(added_uml_model.source_files.values_list("id", flat=True))

                            deleted_files_ids, updated_files_ids, new_submitted_files_ids = _calculate_files_changes(source_files_ids_before_edit, source_files_ids_after_edit, updated_uml_files)
                            schedule_translate_uml_model(request, added_uml_model, source_files_ids_after_edit, updated_files_ids, new_submitted_files_ids, deleted_files_ids)

                        logger.info(f"UML model: {added_uml_model} has been updated.")
                        return redirect("home")
                    else:
                        logger.error(f"UML files: {formset.errors} could not be updated.")
                        messages.error(request, "UML files could not be updated.")
                        return render(request, "update-uml-model.html", {"form": form, "formset": formset})
            else:
                logger.error(f"UML model: {form.errors} could not be updated.")
                messages.error(request, "UML model could not be updated.")
                return render(request, "update-uml-model.html", {"form": form, "formset": formset})

        else:
            form = UpdateUmlModelForm(instance=uml_model_to_update)
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
                extensions_rules: Deque[Set[str]] = deque()
                logger.debug(f"Extensions formset: {list(extension_group_formset)}")
                for form in extension_group_formset:
                    extensions = form.cleaned_data.get('extensions')
                    if extensions:
                        extensions_rules.append(set(ext.strip('. ') for ext in extensions.split(',')))

                logger.debug(f"Extensions rules: {extensions_rules}")
                # Process the regex grouping rules
                regex_rules: Deque[str] = deque()
                for form in regex_group_formset:
                    regex_pattern = form.cleaned_data.get('regex_pattern')
                    if regex_pattern:
                        regex_rules.append(regex_pattern)

                grouped_files = group_files(files, extensions_rules, regex_rules)
                logger.debug(f"Grouped files: {grouped_files}")


                uml_files_for_models = deque()
                uml_models = deque()

                
                while grouped_files:
                    group = grouped_files.pop()
                    model_name = determine_model_name(group)
                    model = UmlModel(name=model_name, description=umlars_app.settings.BULK_UPLOAD_MODEL_DESCRIPTION)
                    uml_models.append(model)

                    model_files = deque()
                    for file in group.files:
                        try:
                            logger.info(f"File id : {id(file)}")
                            decoded_content = decode_file(file)
                        except UnsupportedFileError as ex:
                            warning_message = f"File {file.name} could not be decoded: {ex}"
                            logger.warning(warning_message)
                            messages.warning(request, warning_message)
                            continue

                        uml_file = UmlFile(
                            model=model,
                            filename=file.name,
                            data=decoded_content,
                            format=UmlFile.SupportedFormat.UNKNOWN
                        )

                        model_files.append(uml_file)

                    uml_files_for_models.append(model_files)


                
                if files_form.cleaned_data['dry_run']:
                    return _try_render_forms_for_models(request, uml_models, uml_files_for_models)


                return _try_save_uml_models(request, uml_models, uml_files_for_models)

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


def _try_render_forms_for_models(request: HttpRequest, uml_models: deque[UmlModel], uml_files_for_models: deque[deque[UmlFile]]):
    file_formsets = list()
    # TODO: extra may be needed to be changed ..
    models_initial_data = list()

    model_forms_ids_gen = range(len(uml_models))


    for i in model_forms_ids_gen:
        model = uml_models.pop()
        model_files = uml_files_for_models.pop()
        logger.info(f"Model files: {model_files}")
        models_initial_data.append(model_to_dict(model))

        file_formset_initial_data = list(map(model_to_dict, list(model_files)))
        logger.info(f"file_formset_initial_data: {file_formset_initial_data}")

        file_formset = AddUmlFileFormset(instance=model, prefix=f'source_files_{i}', initial=file_formset_initial_data)
        file_formset.extra = len(file_formset_initial_data)

        logger.info(f"file_formset.initial: {file_formset.initial}")
        file_formsets.append(file_formset)
    
    model_formset = AddUmlModelFormset(prefix=umlars_app.settings.ADD_UML_MODELS_FORMSET_PREFIX, initial=models_initial_data, form_kwargs={"user": request.user})

    return render(request, 'review-bulk-upload.html', {
        'model_forms_with_file_formsets': zip(model_formset.forms, file_formsets),
        'model_formset': model_formset,
        'empty_file_form': AddUmlFileFormset().empty_form,
    })



def _try_save_uml_models(request: HttpRequest, uml_models: deque[UmlModel], uml_files_for_models: deque[deque[UmlFile]]) -> HttpResponse:
    for model, model_files in zip(uml_models, uml_files_for_models):
        try:
            # object may not yet been saved to the database
            source_files_ids_before_edit = set(model.source_files.values_list("id", flat=True))        
        except ValueError as ex:
            logger.warning(f"Model {model} has not been saved to the database yet: {ex}")
            source_files_ids_before_edit = set()
            
        with transaction.atomic():
            model.save()
            model.accessed_by.add(request.user)
            for model_file in model_files:
                model_file.model = model
                model_file.save() 
        

        source_files_ids_after_edit = set(model.source_files.values_list("id", flat=True))        
        deleted_files_ids, updated_files_ids, new_submitted_files_ids = _calculate_files_changes(source_files_ids_before_edit, source_files_ids_after_edit, model_files)
        schedule_translate_uml_model(request, model, source_files_ids_after_edit, updated_files_ids, new_submitted_files_ids, deleted_files_ids)


    messages.success(request, "Files uploaded successfully.")
    return redirect('home')


# TODO: add button to translate manually
async def translate_uml_model(request: HttpRequest, pk: int) -> HttpResponse:
    if (await request.auser()).is_authenticated:
        try:
            model = UmlModel.objects.get(id=pk)
            source_files_ids = set(model.source_files.values_list("id", flat=True))        
            await schedule_translate_uml_model(request, model, source_files_ids)
            messages.success(request, f"Model {model.name} has been sent for translation.")
            return redirect("home")
        except UmlModel.DoesNotExist:
            messages.warning(request, f"Model with id {pk} does not exist.")
            return redirect("home")
    else:
        messages.warning(request, "You need to be logged in to translate the UML model.")
        return redirect("home")


def review_bulk_upload_uml_models(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        if request.method == "POST":
            logger.info(f"POST request received: {request.POST}")
            model_formset = AddUmlModelFormset(request.POST, prefix=umlars_app.settings.ADD_UML_MODELS_FORMSET_PREFIX, form_kwargs={"user": request.user})
            logger.info(f"Processing model forms {list(map(lambda form: form.data, model_formset))}")
            if model_formset.is_valid():
                # This is based on supposition that the order of models in the formset is the same as the order of file groups
                for i, model_form in enumerate(model_formset):
                    logger.info(f"Processing model form {model_form.cleaned_data}")
                    is_form_deleted = model_form.cleaned_data.get('DELETE') in [True, 'on']
                    logger.info(f"Is form deleted: {is_form_deleted}")
                    if is_form_deleted:
                        continue

                    with transaction.atomic():
                        saved_model = model_form.save()
                        saved_model.accessed_by.add(request.user)
                        file_formset = EditUmlFileFormset(request.POST, request.FILES, prefix=f'source_files_{i}', instance=saved_model)
                        if file_formset.is_valid():
                            file_formset.save()
                            
                            source_files_ids = set(saved_model.source_files.values_list("id", flat=True))        
                            schedule_translate_uml_model(request, saved_model, source_files_ids, ids_of_new_submitted_files=source_files_ids)

                        else:
                            messages.warning(request, f"Files for model: {saved_model.name} could not be uploaded. Errors: {file_formset.errors}")
                    
                messages.success(request, "Files uploaded successfully.")
                return redirect('home')
            
            else:
                logger.warning("Invalid formset from review " + str(model_formset.errors))
                messages.warning(request, "Invalid formset from review")
                return render(request, 'review-bulk-upload.html', {
                    'model_formset': model_formset,
                    'empty_file_form': AddUmlFileFormset().empty_form,
                })
        else:
            logger.warning(request, "Only POST supported.")
            messages.warning(request, "Only POST requests supported.")
            model_formset = AddUmlModelFormset(prefix=umlars_app.settings.ADD_UML_MODELS_FORMSET_PREFIX, form_kwargs={"user": request.user})
            return render(request, 'review-bulk-upload.html', {
                'model_formset': model_formset,
                'empty_file_form': AddUmlFileFormset().empty_form,
            })
    else:
        messages.warning(request, "You need to be logged in to review the bulk upload.")
        return redirect("home")


def change_password(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = ChangePasswordForm(request.user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your password was successfully updated!')
                return redirect('home')
            else:
                messages.error(request, 'Please correct the error below.')
        else:
            form = ChangePasswordForm(request.user)
        return render(request, 'change-password.html', {
            'form': form
        })
    else:
        messages.warning(request, "You need to be logged in to change the password.")
        return redirect("home")