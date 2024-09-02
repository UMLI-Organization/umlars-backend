import logging

from umlars_backend import settings


def get_new_sublogger(logger_name: str) -> logging.Logger:
    main_logger_name = next(iter(settings.LOGGING['loggers'].keys()))
    logger = logging.getLogger(main_logger_name).getChild(logger_name)
    return logger