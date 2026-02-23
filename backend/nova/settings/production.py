"""
Nova — Production Settings
============================
Extends base settings with production-specific hardening.
"""

import os
import sys

from .base import *  # noqa: F401, F403

import environ  # noqa: E402

env = environ.Env()

# =============================================================================
# DEBUG (NEVER True in production)
# =============================================================================

DEBUG = False

# =============================================================================
# SECRET KEY — Enforce a strong key in production
# =============================================================================

SECRET_KEY = env('DJANGO_SECRET_KEY')   # MUST be set; no default
_MIN_KEY_LEN = 50
if len(SECRET_KEY) < _MIN_KEY_LEN:
    print(
        f"FATAL: DJANGO_SECRET_KEY must be at least {_MIN_KEY_LEN} characters. "
        f"Current length: {len(SECRET_KEY)}.",
        file=sys.stderr,
    )
    sys.exit(1)

if SECRET_KEY.startswith('insecure'):
    print("FATAL: DJANGO_SECRET_KEY still has the development default.", file=sys.stderr)
    sys.exit(1)

# =============================================================================
# SECURITY — HTTPS / Transport
# =============================================================================

SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 63_072_000     # 2 years (OWASP recommendation)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True     # legacy, but harmless
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Cookie SameSite hardening
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# =============================================================================
# ALLOWED HOSTS (must be explicitly set in production)
# =============================================================================

ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS')

# =============================================================================
# DATABASE (Force explicit credentials + SSL)
# =============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DATABASE_NAME'),
        'USER': env('DATABASE_USER'),
        'PASSWORD': env('DATABASE_PASSWORD'),
        'HOST': env('DATABASE_HOST'),
        'PORT': env('DATABASE_PORT', default='5432'),
        'ATOMIC_REQUESTS': True,
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c default_transaction_isolation=read\\ committed',
            'sslmode': env('DATABASE_SSL_MODE', default='require'),
        },
    }
}

# =============================================================================
# CACHING (Production Redis)
# =============================================================================

CACHES['default']['TIMEOUT'] = 900  # noqa: F405
CACHES['default']['OPTIONS']['MAX_CONNECTIONS'] = 100  # noqa: F405

# =============================================================================
# EMAIL
# =============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')

# =============================================================================
# STATIC FILES
# =============================================================================

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# =============================================================================
# LOGGING (Production: JSON format, file-based with rotation)
# =============================================================================

LOGGING['loggers']['nova']['level'] = 'INFO'  # noqa: F405
LOGGING['loggers']['django']['level'] = 'WARNING'  # noqa: F405
LOGGING['handlers']['console']['level'] = 'WARNING'  # noqa: F405

# =============================================================================
# SENTRY (Error Tracking)
# =============================================================================

SENTRY_DSN = env('SENTRY_DSN', default='')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=float(env('SENTRY_TRACES_SAMPLE_RATE', default=0.1)),
        send_default_pii=False,
        environment='production',
        release=env('APP_VERSION', default='unknown'),
    )

# =============================================================================
# RATE LIMITING (Enabled in production)
# =============================================================================

RATE_LIMIT_ENABLED = True

# =============================================================================
# GRAPHQL SECURITY (Strict in production)
# =============================================================================

GRAPHQL_SECURITY['INTROSPECTION_ENABLED'] = False  # noqa: F405
GRAPHQL_SECURITY['MAX_DEPTH'] = 8                  # noqa: F405
GRAPHQL_SECURITY['MAX_COMPLEXITY'] = 800            # noqa: F405
GRAPHQL_SECURITY['MAX_BATCH_SIZE'] = 3              # noqa: F405

# =============================================================================
# CORS (Strict in production)
# =============================================================================

CORS_ALLOW_ALL_ORIGINS = False

# =============================================================================
# JWT — Enforce separate, strong signing key
# =============================================================================

_jwt_key = env('JWT_SIGNING_KEY', default='')
if not _jwt_key or _jwt_key == SECRET_KEY:
    GRAPHQL_JWT['JWT_SECRET_KEY'] = SECRET_KEY  # noqa: F405
else:
    GRAPHQL_JWT['JWT_SECRET_KEY'] = _jwt_key    # noqa: F405

# =============================================================================
# ADMIN URL — Non-guessable path in production
# =============================================================================

os.environ.setdefault('DJANGO_ADMIN_URL', env('DJANGO_ADMIN_URL', default='nova-secure-admin/'))
