from typing import IO
import logging

from django.core.files.uploadedfile import InMemoryUploadedFile

from umli_backend.settings import LOGGING
from umli_app.exceptions import UnsupportedFileError


main_logger_name = next(iter(LOGGING['loggers'].keys()))
logger = logging.getLogger(main_logger_name).getChild(__name__)


def decode_file(file: IO | InMemoryUploadedFile, encoding: str = 'utf-8') -> str:
    try:
        logger.debug(f"Decoding file: {file} with encoding: {encoding} file_name {file.name} file_id {id(file)}")
        with file.open() as opened_file:
            decoded_data = opened_file.read().decode(encoding)
        return decoded_data
    except UnicodeDecodeError as ex:
        error_message = f"Error decoding file: {file} with encoding: {encoding}.\nError: {ex}"
        logger.error(error_message)
        raise UnsupportedFileError(error_message)