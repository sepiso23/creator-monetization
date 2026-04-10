from .base import *
import environ

env = environ.Env()

# ============================================
# DEVELOPMENT-SPECIFIC SETTINGS
# ============================================

# Debug Mode - Enable in development
DEBUG = True

# Database Configuration
# Use SQLite3 as default database for development
DATABASES = {
    'default': env.db(
        default='sqlite:///db.sqlite3'
    ),
}

# CORS Configuration - Allow all origins for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = (
    *default_headers,
    "x-api-key",  # Allow the custom header
)

CSRF_TRUSTED_ORIGINS = env('CSRF_TRUSTED_ORIGINS', default='http://localhost:5173').split(',')

# Email Backend - Use console for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# REST Framework Development Settings
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
    'djangorestframework_camel_case.render.CamelCaseJSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',  # Enable browsable API in development
)