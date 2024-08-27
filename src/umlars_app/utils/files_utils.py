from django.core.files.uploadedfile import InMemoryUploadedFile
from chardet import detect

from umlars_app.exceptions import UnsupportedFileError
from umlars_app.utils.logging import get_new_sublogger

logger = get_new_sublogger(__name__)


def decode_file(file: InMemoryUploadedFile, encoding: str = None) -> str:
    try:
        logger.debug(f"Decoding file: {file} with encoding: {encoding} file_name {file.name} file_id {id(file)}")
        if file.closed:
            # Closing file would cause an error when trying to read it once again - django closes it itself
            file.open()

        read_file = file.read()
        if not encoding:
            # TODO: this is very expensive operation, consider using some heuristic to guess encoding
            encoding = detect(read_file)['encoding']
    
        decoded_data = read_file.decode(file.charset or encoding)
        return decoded_data

    except UnicodeDecodeError as ex:
        error_message = f"Error decoding file: {file} with encoding: {encoding}.\nError: {ex}"
        logger.error(error_message)
        raise UnsupportedFileError(error_message)