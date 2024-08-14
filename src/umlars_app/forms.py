from abc import ABC, abstractmethod
import re
import logging
from typing import Dict, Any, NamedTuple, Callable, List, Iterator, Deque
from itertools import chain
from functools import partial
from contextlib import contextmanager, ExitStack
from collections import defaultdict, deque

from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import password_validation
from django.utils.safestring import mark_safe
from django.http import QueryDict
from django.core.files.uploadedfile import UploadedFile
from django.utils.datastructures import MultiValueDict

from umlars_app.models import UmlModel, UmlFile, UserAccessToModel
from umlars_app.utils.files_utils import decode_file
from umlars_app.exceptions import UnsupportedFileError
from umlars_app.utils.logging import get_new_sublogger

logger = get_new_sublogger(__name__)


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254,
        label="",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "*Email Address"}
        ),
    )
    first_name = forms.CharField(
        max_length=50,
        label="",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "First Name"}
        ),
        required=False,
    )
    last_name = forms.CharField(
        max_length=70,
        label="",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Last Name"}
        ),
        required=False,
    )


    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)

        self.fields["username"].widget.attrs["class"] = "form-control"
        self.fields["username"].widget.attrs["placeholder"] = "*Username"
        self.fields["username"].label = ""
        self.fields["username"].help_text = mark_safe(
            '<span class="form-text text-muted"><small>Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.</small></span>'
        )

        self.fields["password1"].widget.attrs["class"] = "form-control"
        self.fields["password1"].widget.attrs["placeholder"] = "*Password"
        self.fields["password1"].label = ""
        self.fields["password1"].help_text = mark_safe(
            "<ul class=\"form-text text-muted small\"><li>Your password can't be too similar to your other personal information.</li><li>Your password must contain at least 8 characters.</li><li>Your password can't be a commonly used password.</li><li>Your password can't be entirely numeric.</li></ul>"
        )

        self.fields["password2"].widget.attrs["class"] = "form-control"
        self.fields["password2"].widget.attrs["placeholder"] = "*Confirm Password"
        self.fields["password2"].label = ""
        self.fields["password2"].help_text = mark_safe(
            '<span class="form-text text-muted"><small>Enter the same password as before, for verification.</small></span>'
        )


# TODO: extract common fields to a separate class with CreateUserForm 
class EditUserForm(UserChangeForm):
    email = forms.EmailField(
        max_length=254,
        label="",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "*Email Address"}
        ),
    )
    first_name = forms.CharField(
        max_length=50,
        label="",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "First Name"}
        ),
        required=False,
    )
    last_name = forms.CharField(
        max_length=70,
        label="",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Last Name"}
        ),
        required=False,
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")
        exclude = ("password",)

    def __init__(self, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)

        self.fields["username"].widget.attrs["class"] = "form-control"
        self.fields["username"].widget.attrs["placeholder"] = "*Username"
        self.fields["username"].label = "Username"
        self.fields["username"].help_text = mark_safe(
            '<span class="form-text text-muted"><small>Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.</small></span>'
        )

        self.fields["email"].widget.attrs["class"] = "form-control"
        self.fields["email"].widget.attrs["placeholder"] = "*Email Address"
        self.fields["email"].label = "Email Address"
        self.fields["email"].help_text = mark_safe(
            '<span class="form-text text-muted"><small>Required. 254 characters or fewer.</small></span>'
        )

        self.fields["first_name"].widget.attrs["class"] = "form-control"
        self.fields["first_name"].widget.attrs["placeholder"] = "First Name"
        self.fields["first_name"].label = "First Name"

        self.fields["last_name"].widget.attrs["class"] = "form-control"
        self.fields["last_name"].widget.attrs["placeholder"] = "Last Name"
        self.fields["last_name"].label = "Last Name"

        self.fields["password"].widget.attrs["class"] = "d-none"
        self.fields["password"].label = ""
        self.fields["password"].help_text = mark_safe(
            '<span class="lead">To change the password use <a href=\"change-password/\">this form</a>.</span>'
        )


class ChangePasswordForm(PasswordChangeForm):
    old_password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(
            attrs={'autocomplete': 'current-password', 'autofocus': True, 'class': 'form-control',
                   'placeholder': 'Old Password'}),
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'autocomplete': 'new-password', 'class': 'form-control', 'placeholder': 'New Password'}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(
            attrs={'autocomplete': 'new-password', 'class': 'form-control', 'placeholder': 'Confirm password'}),
    )


class AddUmlModelForm(forms.ModelForm):
    class Meta:
        model = UmlModel
        fields = ("name", "description", "accessed_by")


    name = forms.CharField(
        label="Model Name",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Model Name"}
        ),
        required=True,
    )
    description = forms.CharField(
        label="Description",
        widget=forms.Textarea(
            attrs={"class": "form-control", "placeholder": "Description", 'rows':1, 'cols':1}
        ),
        required=False,
    )

    accessed_by = forms.ModelMultipleChoiceField(
        label="",
        queryset=UserAccessToModel.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input d-none"}),
        required=False,
    )

    def __init__(self, *args, user: User | None = None, **kwargs):
        super(AddUmlModelForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['accessed_by'].initial = [user]


    
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True
    

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


# TODO: MultipleFileField should be used here instead of FileField - it would change significantly the way of handling files in the formset (SplitFormsDataForFilesMixin)
class AddUmlFileForm(forms.ModelForm):
    file = forms.FileField(
        label="Source files",
        widget=MultipleFileInput(attrs={"id":"id-file-input", "class": "form-control file-input", "type": "file", "multiple": True}),
        required=False,
    )

    class Meta:
        model = UmlFile
        fields = ("data", "format", "filename")


    data = forms.CharField(
        label="Raw data",
        widget=forms.Textarea(
            attrs={"class": "form-control", "placeholder": "Raw Data", 'rows':1, 'cols':1}
        ),
        required=False,
    )

    format = forms.ChoiceField(
        label="Format",
        choices=UmlFile.SupportedFormat.choices,
        widget=forms.Select(attrs={"class": "form-control"}),
        required=False,
        initial=UmlFile.SupportedFormat.UNKNOWN
    )

    filename = forms.CharField(
        label="Filename",
        widget=forms.TextInput(
            attrs={"id":"id-filename-input", "class": "form-control filename-input", "placeholder": "Filename"}
        ),
        required=False,
        initial='internal_file'
    )

        
    def clean(self) -> dict:
        cleaned_data =  super(AddUmlFileForm, self).clean()
        data = cleaned_data.get("data")
        logger.debug(f"Data from cleaned data for UmlFile: {data}")

        # Ensure that data is provided (either from manual input or file upload)
        if not data:
            raise forms.ValidationError(
                "You must provide either a source file or formatted data."
            )
        
        return cleaned_data
    

_AddUmlFileFormsetBase = forms.inlineformset_factory(
    UmlModel, UmlFile, form=AddUmlFileForm, 
    extra=1, can_delete=True, can_delete_extra=True, fields=("data", "format", "file", 'filename')
)


_EditUmlFileFormsetBase = forms.inlineformset_factory(
    UmlModel, UmlFile, form=AddUmlFileForm, 
    extra=0, can_delete=True, can_delete_extra=True, fields=("data", "format", "file", 'filename')
)


class FormCopiesConfig(NamedTuple):
    index_of_form_to_copy: int
    number_of_copies: int
    new_values_for_fields: Dict[str, Any | Iterator[Any]]


class FormKeyParts(NamedTuple):
    formset_prefix: str| None = None
    form_index: str| None = None
    field_name: str| None = None
    last_element: str| None = None

    @classmethod
    def try_from_key(cls: type["FormKeyParts"], key: str) -> type["FormKeyParts"]:
        key_parts = key.split('-')
        logger.info(f"Method: try_from_key - key_parts: {key_parts}")
        try:
            key_formset_prefix = key_parts[0]
            key_form_index = int(key_parts[1])
            key_field_name = '-'.join(key_parts[2:])
            key_last_element = key_parts[-1]
        except (IndexError, ValueError):
            return cls()

        return cls(key_formset_prefix, key_form_index, key_field_name, key_last_element)


class ProcessFormDataMixin(ABC):
    @abstractmethod
    def process_data(self, data: QueryDict, *args, **kwargs) -> QueryDict:
        ...


class SplitFormsDataForFilesMixin(ProcessFormDataMixin):
    def process_data(self, data: QueryDict, files: MultiValueDict[str, UploadedFile], prefix: str) -> QueryDict:
        return self.split_forms_data_for_files(data, files, prefix)

    def split_forms_data_for_files(self, data: QueryDict, files: MultiValueDict[str, UploadedFile], prefix: str) -> QueryDict:
        logger.debug(f"Method split_forms_data_for_files - from data: {data} for files: {files}")
        config_for_copies_of_forms_with_multiple_files = self.create_form_copies_config_for_files(data, files, prefix)
        logger.debug(f"Method split_forms_data_for_files - config_for_copies_of_forms_with_multiple_files: {config_for_copies_of_forms_with_multiple_files}")

        if config_for_copies_of_forms_with_multiple_files:
            mutable_post_data = data.copy()
            handler_for_copying_forms = self.create_handler_for_copying_forms(prefix, config_for_copies_of_forms_with_multiple_files)                        
            data = self.apply_to_request_post_elements(mutable_post_data, [handler_for_copying_forms])

        return data

    def create_form_copies_config_for_files(self, post_data: QueryDict, files: MultiValueDict[str, UploadedFile], prefix: str) -> Iterator[FormCopiesConfig]:
        config_for_copies_of_forms_with_multiple_files = list()
        for files_field_name, files_list in files.lists():
            form_index = self.__class__.get_form_index(files_field_name, prefix)
            file_format = post_data.get(f"{prefix}-{form_index}-{self.__class__.FILE_FORMAT_FIELD_NAME}")
            
            filenames = deque()
            decoded_files = deque()

            for file_in_memory in files_list:
                # TODO: make callables - but remember that in such way access is possible only once
                # Also it would require checking if file decoding didnt raise an exception later - during the value retrieval
                # -> this would require a new approach to skipping those files, since callables(retrieval functions) would be added for all files
                # decode_files_callables.append(lambda : decode_file(file_in_memory))
                try:
                    logger.debug(f"Creating formset data - decoding file with name: {file_in_memory.name}")

                    decoded_file = decode_file(file_in_memory)
                except UnsupportedFileError as ex:
                    logger.warning(f"Method: create_form_copies_config_for_files - error during decoding file: {file_in_memory} - {ex}\n Current filenames list: {filenames}\nCurrent decoded files: {decoded_files}")
                    # TODO: Make this class inheirit from the base of Formset class and add here to smth like self.errors information
                    # TODO: add information about failed decoding to some internal dict mapping file name to error message and then pass those information to the user as warnings
                    continue

                decoded_files.append(decoded_file)
                filenames.append(file_in_memory.name)

            number_of_decoded_files=len(decoded_files)

            try:
                assert number_of_decoded_files == len(filenames)
            except AssertionError:
                raise ValueError("Number of files is different than number of filenames.")
            
            
            if decoded_files:
                new_values_for_fields={'data': decoded_files, 'format': file_format, 'filename': filenames}
                config_for_copies_of_forms_with_multiple_files.append(FormCopiesConfig(form_index, number_of_copies=number_of_decoded_files, new_values_for_fields=new_values_for_fields))

        return config_for_copies_of_forms_with_multiple_files

    @staticmethod
    def get_form_index(form_field_name: str, formset_prefix: str | None = None) -> int | None:
        if formset_prefix is not None:
            regex = re.compile(r'^' + formset_prefix + r'-(\d+)-.+$')
        else:
            regex = re.compile(r'^.+-(\d+)-.+$')
        match = regex.match(form_field_name)
        return int(match.group(1)) if match else None


    def create_handler_for_copying_forms(self, formset_prefix: str, forms_copies_config: Iterator[FormCopiesConfig], **kwargs) -> Callable:
        return partial(self.create_copies_of_forms_from_formset, formset_prefix=formset_prefix, forms_copies_config=forms_copies_config, **kwargs)


    @contextmanager
    def create_copies_of_forms_from_formset(self, request_post: QueryDict, formset_prefix: str, forms_copies_config: Iterator[FormCopiesConfig], last_copy_overwrites_original: bool = True) -> Iterator[Callable]:
        form_index_to_copies_config = {form_copies_config.index_of_form_to_copy: form_copies_config for form_copies_config in forms_copies_config}
        logger.debug(f"Method: create_copies_of_forms_from_formset - form_index_to_copies_config: {form_index_to_copies_config}")

        total_forms_key = f"{formset_prefix}-TOTAL_FORMS"
        context_data = dict()

        number_of_indexes_to_reserve = sum(form_copy_config.number_of_copies - (1 if last_copy_overwrites_original else 0) for form_copy_config in forms_copies_config)
        try:
            logger.info(f"Method: create_copies_of_forms_from_formset - number_of_indexes_to_reserve: {number_of_indexes_to_reserve}")
            original_total_forms_number = int(request_post[total_forms_key])
            context_data['current_total_forms_number'] = int(request_post[total_forms_key])
            request_post[total_forms_key] = original_total_forms_number + number_of_indexes_to_reserve

            logger.info(f"Method: create_copies_of_forms_from_formset - total_forms_number after reserving: {request_post[total_forms_key]}")

            context_data['new_form_indexes'] = defaultdict(lambda: defaultdict(dict))
            """
            Sub-dict under the key "new_form_indexes" follows structure:
            { copied_form_index: {
                copy_number: new_form_index
            }
            """
        except (KeyError, ValueError):
            raise ValueError("Specified formset does not exist or TOTAL-FORMS field is not present")

        def is_element_to_be_copied(form_key_parts: FormKeyParts) -> bool:
            is_formset_to_copy = form_key_parts.formset_prefix == formset_prefix
            is_form_to_copy = form_key_parts.form_index in form_index_to_copies_config

            return is_formset_to_copy and is_form_to_copy 

        def get_total_copies_created() -> int:
            return sum(len(copy_to_index_dict) for copied_form_index, copy_to_index_dict in context_data["new_form_indexes"].items())


        def get_value_or_next_from_iterator(value: Any | Iterator[Any]) -> Any:
            logger.info(f"Method: get_value_or_next_from_iterator - value: {value}")
            if isinstance(value, Iterator):
                new_value = next(value)
            elif isinstance(value, (List, Deque)):
                new_value = value.pop()
            else:
                new_value = value
            
            if callable(new_value):
                new_value = new_value()

            logger.info(f"Method: get_value_or_next_from_iterator - new_value: {new_value}")
            logger.info(f"Method: get_value_or_next_from_iterator - received value afterwards: {value}")

            return new_value


        def create_copy_of_form_data(new_form_index: int, old_value: Any, new_values_for_fields: Dict[str, Any], field_name: str) -> None:
            new_key_value_pair = dict()
            new_key = f"{formset_prefix}-{new_form_index}-{field_name}"
            new_value = None

            logger.info(f"Method: create_copy_of_form_data - new_form_index: {new_form_index}, old_value: {old_value}, new_values_for_fields: {new_values_for_fields}, field_name: {field_name}")
            if new_values_for_fields and field_name in new_values_for_fields.keys():
                new_value = get_value_or_next_from_iterator(new_values_for_fields.get(field_name)) 
            else:
                new_value = old_value

            new_key_value_pair[new_key] = new_value 
            return new_key_value_pair

        
        def get_index_for_copy(copies_config: FormCopiesConfig, copy_number: int) -> int:
            new_form_index = context_data['new_form_indexes'][copies_config.index_of_form_to_copy].get(copy_number)
            logger.info(f"Method: get_index_for_copy - copies_config: {copies_config}, copy_number: {copy_number}")
            if new_form_index is None:
                new_form_index = context_data['current_total_forms_number']
                context_data['new_form_indexes'][copies_config.index_of_form_to_copy][copy_number] = new_form_index
                context_data['current_total_forms_number'] += 1
            
            return new_form_index

        def try_create_copies_of_form_data(key: str, value: Any) -> None:
            request_post_update_dict: Dict[str, str] = {}
            form_key_parts = FormKeyParts.try_from_key(key)

            logger.info(f"Method: try_create_copies_of_form_data - key: {key}, value: {value}, form_key_parts: {form_key_parts}")
            if is_element_to_be_copied(form_key_parts):
                logger.info(f"Elemnt is to be copied based on form_key_parts: {form_key_parts}")
                copies_config = form_index_to_copies_config.get(form_key_parts.form_index)

                if last_copy_overwrites_original:
                    copies_numbers = range(copies_config.number_of_copies - 1)
                else:
                    copies_numbers = range(copies_config.number_of_copies)

                for copy_number in copies_numbers:
                    new_form_index = get_index_for_copy(copies_config, copy_number)
                    copy_data_dict = create_copy_of_form_data(new_form_index, value, copies_config.new_values_for_fields, form_key_parts.field_name)

                    logger.info(f"Method: try_create_copies_of_form_data - copy nr: {copy_number} for form id: {new_form_index} - data dict: {copy_data_dict}")               
                    request_post_update_dict.update(copy_data_dict)


                if last_copy_overwrites_original:
                    logger.info(f"Method: try_create_copies_of_form_data - last_copy_overwrites_original: {last_copy_overwrites_original}")
                    copy_data_dict = create_copy_of_form_data(copies_config.index_of_form_to_copy, value, copies_config.new_values_for_fields, form_key_parts.field_name)
                    
                    logger.info(f"Method: try_create_copies_of_form_data - last_copy_overwrites_original - retrieved data dict {copy_data_dict}")
                    request_post_update_dict.update(copy_data_dict)
    
            else:
                logger.info(f"Element is not to be copied based on form_key_parts: {form_key_parts}")

            return request_post_update_dict
        
        try:
            yield try_create_copies_of_form_data
        finally:
            """
            TODO: here there should be checked if all copies were created, if not - change total forms numbers AND all indexes of copies to eliminate the holes
            Code before conflict of indexes (cause by not incrementing in different managers the same base TotalForms):
            request_post[total_forms_key] = context_data['original_total_forms_number'] + get_total_copies_created()
            """
            

    def apply_to_request_post_elements(self, request_post: QueryDict, post_elements_handlers: Iterator[Callable]) -> None:
        """
        Function will edit the provided QueryDict object in place by copying the form with index form_to_copy_index.
        """
        with ExitStack() as stack:
            handlers_and_entered_context_managers = [stack.enter_context(handler) if hasattr((handler := partial_handler(request_post)), '__enter__') else handler for partial_handler in post_elements_handlers]
            iterators_over_dicts_for_request_post_update: List[Iterator] = list()

            logger.info(F"Method: apply_to_request_post_elements - request_post after context managers entered: {request_post}")        
            for key, value in request_post.items():
                # TODO: remove this list()
                logger.info(F"Method: apply_to_request_post_elements - key: {key}, value: {value}")
                iterators_over_dicts_for_request_post_update.append(list(map(lambda handler: handler(key, value), handlers_and_entered_context_managers)))


            logger.info(f"Method: apply_to_request_post_elements - iterators_over_dicts_for_request_post_update: {iterators_over_dicts_for_request_post_update}")
            for update_dict in chain.from_iterable(iterators_over_dicts_for_request_post_update):
                logger.info(f"Method: apply_to_request_post_elements - update_dict: {update_dict}")
                request_post.update(update_dict)

        return request_post


class AddUmlFileFormset(_AddUmlFileFormsetBase, SplitFormsDataForFilesMixin):
    FILE_FORMAT_FIELD_NAME = 'format'
    
    def __init__(self, data: Any | None = None, files: Any | None = None, instance: Any | None = None, save_as_new: bool = None, prefix: Any | None = None, queryset: Any | None = None, **kwargs: Any) -> None:
        if data is not None and files is not None and prefix is not None:
            data = self.process_data(data, files, prefix)
        
        logger.info(f"Method: AddUmlFileFormset.__init__ - data: {data}, files: {files}, instance: {instance}, save_as_new: {save_as_new}, prefix: {prefix}, queryset: {queryset}, kwargs: {kwargs}")
        super().__init__(data, files=None, instance=instance, save_as_new=save_as_new, prefix=prefix, queryset=queryset, **kwargs)


class EditUmlFileFormset(_EditUmlFileFormsetBase, SplitFormsDataForFilesMixin):
    FILE_FORMAT_FIELD_NAME = 'format'
    
    def __init__(self, data: Any | None = None, files: Any | None = None, instance: Any | None = None, save_as_new: bool = None, prefix: Any | None = None, queryset: Any | None = None, **kwargs: Any) -> None:
        if data is not None and files is not None and prefix is not None:
            data = self.process_data(data, files, prefix)
        
        logger.info(f"Method: AddUmlFileFormset.__init__ - data: {data}, files: {files}, instance: {instance}, save_as_new: {save_as_new}, prefix: {prefix}, queryset: {queryset}, kwargs: {kwargs}")
        super().__init__(data, files=None, instance=instance, save_as_new=save_as_new, prefix=prefix, queryset=queryset, **kwargs)



class GroupingRuleForm(forms.Form):
    ...


class ExtensionsGroupingRuleForm(GroupingRuleForm):
    extensions = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'e.g. .uml,.notation'}),
        label="Extensions to join (comma-separated)",
        initial=" uml, notation",
        help_text="Files with the same names will be joined into one model, if they have formats from the same group.",
        required=False
    )


class RegexGroupingRuleForm(GroupingRuleForm):
    regex_pattern = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Regex grouping pattern'}),
        required=False,
        label="Regex pattern",
        help_text="Files will be joined into one model, if they have identical values for all groups from the given regex."
    )


class FilesGroupingForm(forms.Form):
    dry_run = forms.BooleanField(
        required=False,
        label="Dry run (review groups before final upload)",
        widget=forms.CheckboxInput(attrs={"class": "form-switch"}),
        initial=True
    )
    files = MultipleFileField(
        label="Upload files:",
        widget=MultipleFileInput(attrs={"id": "id-file-input", "class": "form-control", "multiple": True}),
    )


ExtensionsGroupingFormSet = forms.formset_factory(ExtensionsGroupingRuleForm, extra=1)
RegexGroupingFormSet = forms.formset_factory(RegexGroupingRuleForm, extra=0)


AddUmlModelFormset = forms.formset_factory(form=AddUmlModelForm, extra=0, can_delete=True, can_delete_extra=True)


def formset_factory_with_overriden_attributes(formset_base_class: type["forms.BaseFormSet"], **attributes_to_override) -> type["forms.BaseFormSet"]:
    class FormsetWithAttributesOverriden(formset_base_class):
        for attr_name, attr_value in attributes_to_override.items():
            vars()[attr_name] = attr_value


    return FormsetWithAttributesOverriden

def increase_forms_count_in_formset(formset: forms.BaseFormSet, increment: int) -> None:
    management_form_data = formset.management_form.initial
    logger.info(f"Method: increase_forms_count_in_formset - management_form_data: {management_form_data}")

    incremented_total_forms = int(management_form_data['TOTAL_FORMS']) + increment
    incremented_initial_forms = int(management_form_data['INITIAL_FORMS']) + increment


    management_form_data['TOTAL_FORMS'] = incremented_total_forms
    management_form_data['INITIAL_FORMS'] = incremented_initial_forms

    formset.management_form.initial = management_form_data
    formset._total_form_count = incremented_total_forms
    formset._initial_form_count = incremented_initial_forms

    logger.info(f"Changed management form initial data: {formset.management_form.initial}")
    # formset.extra = 2



# def add(formset: forms.BaseFormSet, **kwargs: Any):
#     tfc = formset.total_form_count()
#     formset.forms.append(formset._construct_form(tfc, **kwargs))
#     formset.forms[tfc].is_bound = False

#     # make data mutable
#     formset.data = formset.data.copy()

#     # increase hidden form counts
#     total_count_name = '%s-%s' % (formset.management_form.prefix, TOTAL_FORM_COUNT)
#     initial_count_name = '%s-%s' % (formset.management_form.prefix, INITIAL_FORM_COUNT)
#     formset.data[total_count_name] = formset.management_form.cleaned_data[TOTAL_FORM_COUNT] + 1
#     formset.data[initial_count_name] = formset.management_form.cleaned_data[INITIAL_FORM_COUNT] + 1


# def add_form_to_formset(formset: forms.BaseFormSet, form_data: Dict[str, Any]) -> None:
#     logger.debug(f"Method: add_form_to_formset - form_data: {form_data}")
#     # Get the management form data
#     management_form_data = formset.management_form.initial
#     total_forms = int(management_form_data['TOTAL_FORMS'])

#     # Increment the total forms count
#     management_form_data['TOTAL_FORMS'] = total_forms + 1

#     # Create a new form instance with initial data if needed
#     import copy
#     new_form = copy.deepcopy(formset.empty_form)
#     new_form.prefix = formset.prefix
#     new_form.initial = form_data

#     # new_form = formset.empty_form
#     # new_form.prefix = formset.prefix
#     # new_form.initial = form_data
    
#     # new_form = formset.form(initial=form_data, prefix=f'{formset.prefix}-{total_forms}')
#     logger.debug(f"Method: add_form_to_formset - new_form initial data: {new_form.initial}")
#     # logger.info(f"New form: {new_form}")
#     # Append the new form to the formset's forms
#     formset.forms.append(new_form)

#     # Update the formset's management form data
#     formset.management_form.initial = management_form_data
#     formset._total_form_count = total_forms + 1

