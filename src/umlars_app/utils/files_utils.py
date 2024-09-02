from django.core.files.uploadedfile import InMemoryUploadedFile
from chardet import detect

from umlars_app.exceptions import UnsupportedFileError
from umlars_app.utils.logging import get_new_sublogger

logger = get_new_sublogger(__name__)


def decode_file(file: InMemoryUploadedFile, encoding: str = 'utf-8') -> str:
    try:
        logger.debug(f"Decoding file: {file} with encoding: {encoding} file_name {file.name} file_id {id(file)}")
        if file.closed:
            # Closing file would cause an error when trying to read it once again - django closes it itself
            file.open()

        read_file = file.read()

        try:
            decoded_data = read_file.decode(encoding)
        except UnicodeDecodeError as ex:
            logger.warning(f"Error decoding file: {file} with encoding: {encoding}.\nError: {ex}")
            # If encoding is not provided, try to detect it
            # This is expensive operation, so it is done only if the encoding is not provided
            encoding = detect(read_file)['encoding']
            decoded_data = read_file.decode(encoding)

        return decoded_data

    except UnicodeDecodeError as ex:
        error_message = f"Error decoding file: {file} with encoding: {encoding}.\nError: {ex}"
        logger.error(error_message)
        raise UnsupportedFileError(error_message)
