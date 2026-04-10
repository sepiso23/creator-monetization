from .base import *
import environ
import os

env = environ.Env(DEBUG=(bool, False))

# ============================================
# PRODUCTION-SPECIFIC SETTINGS
# ============================================

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

os.environ.setdefault('DJANGO_AUTO_SETUP', 'False')

# Debug Mode - Disable in production
DEBUG = env('DEBUG', default=False)

# Database Configuration
# Read DATABASE_URL from environment variable (e.g., PostgreSQL connection string)
DATABASES = {
    'default': env.db()
}

# CORS Configuration for production
CORS_ALLOWED_ORIGINS = env(
    'CORS_ALLOWED_ORIGINS', 
    default='http://localhost:5173,http://127.0.0.1:5173'
).split(',')

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = (
    *default_headers,
    "x-api-key",  # Allow the custom header
)

CSRF_TRUSTED_ORIGINS = env(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost:5173'
).split(',')

# Email Backend - Use SMTP for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# REST Framework Production Settings
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
    'djangorestframework_camel_case.render.CamelCaseJSONRenderer',
)

# Spectacular Settings for Production
SPECTACULAR_SETTINGS['SERVE_PERMISSIONS'] = ['rest_framework.permissions.AllowAny']
SPECTACULAR_SETTINGS['SERVERS'] = [{'url': 'https://backend.tipzed.space/api'}]

# Configure Logging for Production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}