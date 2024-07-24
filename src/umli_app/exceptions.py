class UnsupportedFileError(Exception):
    """
    Raised when received file can't be handled in the expected way.
    """


class QueueUnavailableError(Exception):
    """
    Raised when the message broker queue is not available.
    """