import logging
import sys

from app.core.settings import settings


LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "%(message)s"
)


def setup_logger():

    logger = logging.getLogger("neednow")

    logger.setLevel(settings.LOG_LEVEL)

    formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()