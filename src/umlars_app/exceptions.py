class UnsupportedFileError(Exception):
    """
    Raised when received file can't be handled in the expected way.
    """


class QueueUnavailableError(Exception):
    """
    Raised when the message broker queue is not available.
    """


class ServiceConnectionError(Exception):
    """Service outage error."""


class NotYetAvailableError(Exception):
    """Service not yet available error."""


class InputDataError(Exception):
    """Input data error."""
