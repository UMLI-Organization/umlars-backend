from typing import IO
import logging

from django.core.files.uploadedfile import InMemoryUploadedFile

from umli_backend.settings import LOGGING
from umli_app.exceptions import UnsupportedFileError
from umli_app.utils.logging import get_new_sublogger

logger = get_new_sublogger(__name__)


def decode_file(file: InMemoryUploadedFile, encoding: str = 'utf-8') -> str:
    try:
        logger.debug(f"Decoding file: {file} with encoding: {encoding} file_name {file.name} file_id {id(file)}")
        if file.closed:
            # Closing file would cause an error when trying to read it once again - django closes it itself
            file.open()

        decoded_data = file.read().decode(encoding)


        return decoded_data
    except UnicodeDecodeError as ex:
        error_message = f"Error decoding file: {file} with encoding: {encoding}.\nError: {ex}"
        logger.error(error_message)
        raise UnsupportedFileError(error_message)