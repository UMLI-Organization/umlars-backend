import re
from typing import Dict, Any, NamedTuple, Callable, List, Iterator, Iterable, Deque
from itertools import chain
from functools import partial
from contextlib import contextmanager, ExitStack
from collections import defaultdict

from django.contrib import messages
from django.http import QueryDict

request_l = []
def get_form_index(form_field_name: str, formset_prefix: str|None = None) -> int | None:
    if formset_prefix is not None:
        regex = re.compile(r'^' + formset_prefix + r'-(\d+)-.+$')
    else:
        regex = re.compile(r'^.+-(\d+)-.+$')
    match = regex.match(form_field_name)
    return int(match.group(1)) if match else None


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
        messages.error(request_l[0], f"key_parts: {key_parts}")
        try:
            key_formset_prefix = key_parts[0]
            key_form_index = int(key_parts[1])
            key_field_name = '-'.join(key_parts[2:])
            key_last_element = key_parts[-1]
        except (IndexError, ValueError):
            return cls()

        return cls(key_formset_prefix, key_form_index, key_field_name, key_last_element)


def create_handler_for_copying_forms(formset_prefix: str, forms_copies_config: Iterator[FormCopiesConfig], **kwargs) -> Callable:
    return partial(create_copies_of_forms_from_formset, formset_prefix=formset_prefix, forms_copies_config=forms_copies_config, **kwargs)


@contextmanager
def create_copies_of_forms_from_formset(request_post: QueryDict, formset_prefix: str, forms_copies_config: Iterator[FormCopiesConfig], ignore_deleted: bool =True, last_copy_overwrites_original: bool = True) -> None:
    form_index_to_copies_config = {form_copies_config.index_of_form_to_copy: form_copies_config for form_copies_config in forms_copies_config}

    total_forms_key = f"{formset_prefix}-TOTAL_FORMS"
    context_data = dict()

    number_of_indexes_to_reserve = sum(form_copy_config.number_of_copies for form_copy_config in forms_copies_config) - (1 if last_copy_overwrites_original else 0)
    try:
        original_total_forms_number = int(request_post[total_forms_key])
        context_data['current_total_forms_number'] = int(request_post[total_forms_key])
        request_post[total_forms_key] = original_total_forms_number + number_of_indexes_to_reserve

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
        is_deleted = form_key_parts.last_element == 'DELETE'
        is_formset_to_copy = form_key_parts.formset_prefix == formset_prefix
        is_form_to_copy = form_key_parts.form_index in form_index_to_copies_config

        return is_formset_to_copy and is_form_to_copy and not (is_deleted and ignore_deleted) 

    def get_total_copies_created() -> int:
        return sum(len(copy_to_index_dict) for copied_form_index, copy_to_index_dict in context_data["new_form_indexes"].items())


    def get_value_or_next_from_iterator(value: Any | Iterator[Any]) -> Any:
        messages.success(request_l[0], f"value received: {value}")
        if isinstance(value, Iterator):
            new_value = next(value)
        elif isinstance(value, (List, Deque)):
            new_value = value.pop()
        else:
            new_value = value
        
        if callable(new_value):
            new_value = new_value()

        messages.success(request_l[0], f"value received - after: {value}")

        messages.success(request_l[0], f"new_value: {new_value}")

        return new_value


    def create_copy_of_form_data(new_form_index: int, old_value: Any, new_values_for_fields: Dict[str, Any], field_name: str) -> None:
        new_key_value_pair = dict()
        new_key = f"{formset_prefix}-{new_form_index}-{field_name}"

        messages.success(request_l[0], f"new_values_for_fields: {new_values_for_fields}, field: {field_name}")
        new_value = get_value_or_next_from_iterator(new_values_for_fields.get(field_name)) if new_values_for_fields else old_value
        new_key_value_pair[new_key] = new_value 
        return new_key_value_pair

    
    def get_index_for_copy(copies_config: FormCopiesConfig, copy_number: int) -> int:
        new_form_index = context_data['new_form_indexes'][copies_config.index_of_form_to_copy].get(copy_number)
        messages.error(request_l[0], f"get_index_for_copy -new_form_index that may be none: {new_form_index}")
        if new_form_index is None:
            new_form_index = context_data['current_total_forms_number']
            context_data['new_form_indexes'][copies_config.index_of_form_to_copy][copy_number] = new_form_index
            context_data['current_total_forms_number'] += 1
        
        return new_form_index

    def try_create_copies_of_form_data(key: str, value: Any) -> None:
        request_post_update_dict: Dict[str, str] = {}
        form_key_parts = FormKeyParts.try_from_key(key)

        messages.warning(request_l[0], f"form_key_parts: {form_key_parts}")
        messages.warning(request_l[0], f"is_to_be_copied: {is_element_to_be_copied(form_key_parts)}")
        if is_element_to_be_copied(form_key_parts):
            copies_config = form_index_to_copies_config.get(form_key_parts.form_index)

            if last_copy_overwrites_original:
                copies_numbers = range(copies_config.number_of_copies - 1)
            else:
                copies_numbers = range(copies_config.number_of_copies)

            for copy_number in copies_numbers:
                new_form_index = get_index_for_copy(copies_config, copy_number)


                copy_data_dict = create_copy_of_form_data(new_form_index, value, copies_config.new_values_for_fields, form_key_parts.field_name)
                messages.success(request_l[0], f"copy nr: {copy_number} for form id: {new_form_index} - data dict: {copy_data_dict}")
                request_post_update_dict.update(copy_data_dict)


            if last_copy_overwrites_original:
                messages.success(request_l[0], f"last_copy_overwrites_original - request_post_update_dict: {request_post_update_dict}")
                copy_data_dict = create_copy_of_form_data(copies_config.index_of_form_to_copy, value, copies_config.new_values_for_fields, form_key_parts.field_name)
                messages.success(request_l[0], f"last_copy_overwrites_original: {copy_data_dict}")
                request_post_update_dict.update(copy_data_dict)
 


        return request_post_update_dict
                    
    # TODO: -suggested but why 
    # if key_parts[-1] == 'id':
    #     return
    
    try:
        yield try_create_copies_of_form_data
    finally:
        ...
        # TODO: here there should be checked if all copies were created, if not - change total forms numbers AND all indexes of copies to eliminate the holes
        # request_post[total_forms_key] = context_data['original_total_forms_number'] + get_total_copies_created()


def apply_to_request_post_elements(request_post: QueryDict, post_elements_handlers: Iterator[Callable], request) -> None:
    """
    Function will edit the provided QueryDict object in place by copying the form with index form_to_copy_index.
    """
    request_l.append(request)

    with ExitStack() as stack:
        handlers_and_entered_context_managers = [stack.enter_context(handler) if hasattr((handler := partial_handler(request_post)), '__enter__') else handler for partial_handler in post_elements_handlers]
        iterators_over_dicts_for_request_post_update: List[Iterator] = list()
        
        # dicts_to_update_post: Iterator[Dict[str,str]]
        messages.error(request_l[0], f"request_post after context managers entered: {list(request_post.items())}")
        for key, value in request_post.items():
            # Make passing function for handling the found key possible
            # TODO: remove this list()
            messages.error(request_l[0], f"k: {key}, v: {value}")
            iterators_over_dicts_for_request_post_update.append(list(map(lambda handler: handler(key, value), handlers_and_entered_context_managers)))

        messages.error(request_l[0], f"iterators_over_dicts_for_request_post_update: {iterators_over_dicts_for_request_post_update}")
        for update_dict in chain.from_iterable(iterators_over_dicts_for_request_post_update):
            messages.error(request_l[0], f"update_dict: {update_dict}")
            request_post.update(update_dict)

    return request_post
    
    # """
    # handling -id field"""
    # id_key = f"{formset_prefix}-{form_to_copy_index}-id"
    # id_value = request_post[id_key]
    # request_post[id_key.replace(str(form_to_copy_index), str(form_to_copy_index + 1))] = id_value
    # fields_to_pop = ['id', 'DELETE']

