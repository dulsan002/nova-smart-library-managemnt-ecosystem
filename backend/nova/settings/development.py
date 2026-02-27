"""
Nova — Development Settings
============================
Extends base settings with development-specific overrides.
"""

from .base import *  # noqa: F401, F403

# =============================================================================
# DEBUG
# =============================================================================

DEBUG = True

# =============================================================================
# ADDITIONAL APPS (DEV ONLY)
# =============================================================================

INSTALLED_APPS += [  # noqa: F405
    'debug_toolbar',
]

MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')  # noqa: F405

INTERNAL_IPS = ['127.0.0.1', 'localhost']

# =============================================================================
# DATABASE (Allow SQLite fallback for quick dev)
# =============================================================================

import environ  # noqa: E402

env = environ.Env()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DATABASE_NAME', default='nova_db'),
        'USER': env('DATABASE_USER', default='nova_user'),
        'PASSWORD': env('DATABASE_PASSWORD', default='nova_password'),
        'HOST': env('DATABASE_HOST', default='localhost'),
        'PORT': env('DATABASE_PORT', default='5433'),
        'ATOMIC_REQUESTS': True,
        'CONN_MAX_AGE': 0,  # Don't persist connections in dev
    }
}

# =============================================================================
# EMAIL
# =============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# =============================================================================
# CORS (Allow all in dev)
# =============================================================================

CORS_ALLOW_ALL_ORIGINS = True

# =============================================================================
# CACHING (Use local memory in dev if Redis unavailable)
# =============================================================================

def _redis_available():
    """Check if Redis is reachable on localhost:6379."""
    import socket
    try:
        s = socket.create_connection(('localhost', 6379), timeout=1)
        s.close()
        return True
    except OSError:
        return False

if not _redis_available():
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'nova-dev-cache',
        },
        'sessions': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'nova-dev-sessions',
        },
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'
    # Run Celery tasks synchronously (in-process) when Redis is down
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'cache+memory://'
    CELERY_BEAT_SCHEDULE = {}  # Disable periodic tasks without Redis
    print('\n⚠  Redis not available — using local memory cache, DB sessions & eager Celery.\n')

# =============================================================================
# LOGGING OVERRIDES
# =============================================================================

LOGGING['loggers']['nova']['level'] = 'DEBUG'  # noqa: F405
LOGGING['loggers']['django']['level'] = 'DEBUG'  # noqa: F405

# =============================================================================
# SECURITY (Relaxed for development)
# =============================================================================

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# =============================================================================
# RATE LIMITING (Disabled in dev)
# =============================================================================

RATE_LIMIT_ENABLED = False

# =============================================================================
# DEBUG TOOLBAR
# =============================================================================

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
    'INSERT_BEFORE': '</body>',
    'RENDER_PANELS': True,
    'IS_RUNNING_TESTS': False,
}
