"""
Nova — Test Settings
=====================
Optimized for fast test execution.
"""

from .base import *  # noqa: F401, F403

# =============================================================================
# DEBUG
# =============================================================================

DEBUG = False

# =============================================================================
# DATABASE (Use faster settings for tests)
# =============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'ATOMIC_REQUESTS': True,
        'TEST': {
            'NAME': ':memory:',
        },
    }
}

# =============================================================================
# PASSWORD HASHING (Fast for tests)
# =============================================================================

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# =============================================================================
# CACHING (In-memory for tests)
# =============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'sessions': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
}

# =============================================================================
# EMAIL
# =============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# =============================================================================
# CELERY (Synchronous for tests)
# =============================================================================

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# =============================================================================
# RATE LIMITING (Disabled in tests)
# =============================================================================

RATE_LIMIT_ENABLED = False

# =============================================================================
# LOGGING (Minimal in tests)
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
        'level': 'CRITICAL',
    },
}

# =============================================================================
# MEDIA (Temporary for tests)
# =============================================================================

import tempfile  # noqa: E402

MEDIA_ROOT = tempfile.mkdtemp()

# =============================================================================
# SECRET KEY (Fixed for tests)
# =============================================================================

SECRET_KEY = 'test-secret-key-not-for-production-use-only-for-testing-purposes'
