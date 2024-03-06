from .base import *

# Development

INSTALLED_APPS = [
                     "drf_spectacular",

                     "daphne",
                     "debug_toolbar",
                 ] + INSTALLED_APPS

MIDDLEWARE = [
                 'debug_toolbar.middleware.DebugToolbarMiddleware'
             ] + MIDDLEWARE
INTERNAL_IPS = ["127.0.0.1", "localhost"]
DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda request: True}
LOGGING = {
    "version": 1,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django.db.backends": {
            "level": "DEBUG",
        },
    },
    "root": {
        "handlers": ["console"],
    },
}
