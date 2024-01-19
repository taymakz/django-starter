from .base import *


ALLOWED_HOSTS = ['*']

INSTALLED_APPS  =  [
   'daphne',
   'drf_spectacular',
] + INSTALLED_APPS



LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
        },
    },
    'root': {
        'handlers': ['console'],
    }
}