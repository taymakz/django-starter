from .base import *

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
                     'daphne',
                     'drf_spectacular',
                     'debug_toolbar',
                 ] + INSTALLED_APPS

# MIDDLEWARE = [
#                  'debug_toolbar.middleware.DebugToolbarMiddleware'
#              ] + MIDDLEWARE
INTERNAL_IPS = [

    '127.0.0.1',
    'localhost'
]
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
