from typing import Type, Callable
import time
from functools import wraps

from umlars_app.exceptions import ServiceConnectionError, NotYetAvailableError


def retry(reconnect_attempts: int = 5, sleep_seconds_between_recconnects: int = 5, exception_class_raised_when_all_attempts_failed: Type["Exception"] = ServiceConnectionError) -> Callable:
    def wrapper(function_to_attempt: Callable) -> Callable:
        @wraps(function_to_attempt)
        def inner(*args, **kwargs):
            max_reconnect_attempt_number = reconnect_attempts - 1
            for reconnect_attempt_number in range(reconnect_attempts):
                try:
                    return function_to_attempt(*args, **kwargs)
                except NotYetAvailableError as ex:
                    if reconnect_attempt_number == max_reconnect_attempt_number:
                        raise exception_class_raised_when_all_attempts_failed(str(ex)) from ex
                    time.sleep(sleep_seconds_between_recconnects)

        return inner
    return wrapper
