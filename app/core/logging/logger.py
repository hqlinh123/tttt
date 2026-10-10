import logging
import sys
from logging.config import dictConfig


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "default": {
            "format": (
                "[%(asctime)s] "
                "[%(levelname)s] "
                "[%(name)s] "
                "%(message)s"
            ),
        },
        "access": {
            "format": (
                "[%(asctime)s] "
                "[ACCESS] "
                "%(message)s"
            ),
        },
    },

    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
        },
    },

    "loggers": {
        # App loggers
        "app": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False,
        },

        # Uvicorn loggers
        "uvicorn.error": {
            "level": "INFO",
        },
        "uvicorn.access": {
            "handlers": ["access"],
            "level": "INFO",
            "propagate": False,
        },
    },

    "root": {
        "handlers": ["default"],
        "level": "INFO",
    },
}


def setup_logging() -> None:
    """Call once at application startup"""
    dictConfig(LOGGING_CONFIG)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
