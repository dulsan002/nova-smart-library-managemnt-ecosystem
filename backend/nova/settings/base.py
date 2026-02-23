"""
Nova Intelligent Digital Library — Base Settings
=================================================
Shared settings for all environments.
Environment-specific settings override these in development.py, production.py, test.py.
"""

import os
from pathlib import Path
from datetime import timedelta

import environ

# =============================================================================
# PATH CONFIGURATION
# =============================================================================

# backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Initialize django-environ
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
)

# Read .env file if it exists
env_file = BASE_DIR / '.env'
if env_file.exists():
    environ.Env.read_env(str(env_file))

# =============================================================================
# CORE DJANGO SETTINGS
# =============================================================================

SECRET_KEY = env('DJANGO_SECRET_KEY', default='insecure-dev-key-change-in-production')

DEBUG = env('DJANGO_DEBUG', default=True)

ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'graphene_django',
    'corsheaders',
    'django_filters',
    'django_extensions',
]

LOCAL_APPS = [
    'apps.common',
    'apps.identity',
    'apps.catalog',
    'apps.circulation',
    'apps.digital_content',
    'apps.engagement',
    'apps.intelligence',
    'apps.governance',
    'apps.asset_management',
    'apps.hr',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# =============================================================================
# MIDDLEWARE
# =============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'nova.middleware.request_logging.RequestLoggingMiddleware',
    'nova.middleware.security_headers.SecurityHeadersMiddleware',
    'nova.middleware.graphql_security.GraphQLSecurityMiddleware',
    'nova.middleware.rate_limiting.RateLimitingMiddleware',
    'nova.middleware.exception_handler.ExceptionHandlerMiddleware',
]

ROOT_URLCONF = 'nova.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'nova.wsgi.application'
ASGI_APPLICATION = 'nova.asgi.application'

# =============================================================================
# DATABASE
# =============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DATABASE_NAME', default='nova_db'),
        'USER': env('DATABASE_USER', default='nova_user'),
        'PASSWORD': env('DATABASE_PASSWORD', default='nova_password'),
        'HOST': env('DATABASE_HOST', default='localhost'),
        'PORT': env('DATABASE_PORT', default='5432'),
        'ATOMIC_REQUESTS': True,
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# =============================================================================
# CUSTOM USER MODEL
# =============================================================================

AUTH_USER_MODEL = 'identity.User'

# =============================================================================
# PASSWORD VALIDATION & HASHING
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# =============================================================================
# STATIC & MEDIA FILES
# =============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static' / 'collected'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = env('MEDIA_ROOT', default=str(BASE_DIR / 'media'))

# =============================================================================
# DEFAULT PRIMARY KEY
# =============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# REDIS & CACHING
# =============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_CACHE_URL', default='redis://localhost:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'MAX_CONNECTIONS': 50,
        },
        'KEY_PREFIX': 'nova',
        'TIMEOUT': 900,  # 15 minutes default TTL
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_SESSION_URL', default='redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'nova_session',
        'TIMEOUT': 1800,  # 30 minutes
    },
}

# =============================================================================
# CELERY CONFIGURATION
# =============================================================================

CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/3')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/3')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutes soft limit
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True

CELERY_TASK_QUEUES = {
    'default': {'exchange': 'default', 'routing_key': 'default'},
    'engagement': {'exchange': 'engagement', 'routing_key': 'engagement'},
    'intelligence': {'exchange': 'intelligence', 'routing_key': 'intelligence'},
    'verification': {'exchange': 'verification', 'routing_key': 'verification'},
    'maintenance': {'exchange': 'maintenance', 'routing_key': 'maintenance'},
}

CELERY_TASK_DEFAULT_QUEUE = 'default'

CELERY_BEAT_SCHEDULE = {
    'detect-overdue-transactions': {
        'task': 'apps.circulation.tasks.overdue_detection.detect_overdue_transactions',
        'schedule': timedelta(hours=1),
        'options': {'queue': 'maintenance'},
    },
    'cleanup-expired-sessions': {
        'task': 'apps.digital_content.tasks.session_cleanup.cleanup_expired_sessions',
        'schedule': timedelta(minutes=15),
        'options': {'queue': 'maintenance'},
    },
    'evaluate-daily-streaks': {
        'task': 'apps.engagement.tasks.streak_evaluation.evaluate_daily_streaks',
        'schedule': timedelta(days=1),
        'options': {'queue': 'engagement'},
    },
    'refresh-stale-recommendations': {
        'task': 'apps.intelligence.tasks.recommendation_refresh.refresh_stale_recommendations',
        'schedule': timedelta(hours=6),
        'options': {'queue': 'intelligence'},
    },
    # --- AI/ML periodic tasks (Role 5) ---
    'predict-overdue-risks': {
        'task': 'intelligence.predict_overdue_risks',
        'schedule': timedelta(hours=4),
        'options': {'queue': 'intelligence'},
    },
    'analyze-churn-risks': {
        'task': 'intelligence.analyze_churn_risks',
        'schedule': timedelta(days=7),
        'options': {'queue': 'intelligence'},
    },
    'auto-tag-new-books': {
        'task': 'intelligence.auto_tag_new_books',
        'schedule': timedelta(hours=12),
        'options': {'queue': 'intelligence'},
    },
    'deliver-notifications': {
        'task': 'intelligence.deliver_notifications',
        'schedule': timedelta(minutes=5),
        'options': {'queue': 'default'},
    },
    'compute-book-embeddings': {
        'task': 'intelligence.compute_book_embeddings_batch',
        'schedule': timedelta(hours=6),
        'options': {'queue': 'intelligence'},
    },
    'compute-trending-books': {
        'task': 'intelligence.compute_trending_books',
        'schedule': timedelta(hours=3),
        'options': {'queue': 'intelligence'},
    },
    'weekly-model-training': {
        'task': 'intelligence.run_model_training',
        'schedule': timedelta(days=7),
        'kwargs': {'pipeline': 'all'},
        'options': {'queue': 'intelligence'},
    },
}

# =============================================================================
# GRAPHQL (GRAPHENE)
# =============================================================================

GRAPHENE = {
    'SCHEMA': 'nova.schema.schema',
    'MIDDLEWARE': [
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
    ],
}

GRAPHQL_JWT = {
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_EXPIRATION_DELTA': timedelta(
        minutes=int(env('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', default=15))
    ),
    'JWT_REFRESH_EXPIRATION_DELTA': timedelta(
        days=int(env('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=7))
    ),
    'JWT_SECRET_KEY': env('JWT_SIGNING_KEY', default=SECRET_KEY),
    'JWT_ALGORITHM': 'HS256',
    'JWT_AUTH_HEADER_PREFIX': 'Bearer',
    'JWT_ALLOW_ANY_CLASSES': [
        'graphql_jwt.mutations.ObtainJSONWebToken',
        'graphql_jwt.mutations.Verify',
        'graphql_jwt.mutations.Refresh',
    ],
}

AUTHENTICATION_BACKENDS = [
    'graphql_jwt.backends.JSONWebTokenBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# =============================================================================
# GRAPHQL SECURITY (depth / complexity / introspection)
# =============================================================================

GRAPHQL_SECURITY = {
    'MAX_DEPTH': int(env('GQL_MAX_DEPTH', default=10)),
    'MAX_COMPLEXITY': int(env('GQL_MAX_COMPLEXITY', default=1000)),
    'MAX_ALIASES': 15,
    'MAX_QUERY_SIZE_BYTES': 10_000,       # 10 KB
    'MAX_BATCH_SIZE': 5,
    'INTROSPECTION_ENABLED': None,        # None = follow DEBUG; set True/False to override
    'FIELD_COSTS': {
        'books': 5,
        'users': 5,
        'allBorrows': 5,
        'auditLogs': 5,
        'recommendations': 8,
        'searchBooks': 10,
        'semanticSearch': 15,
        'readingPatterns': 5,
        'collectionGaps': 8,
        'overdueRiskPredictions': 10,
    },
}

# =============================================================================
# CORS
# =============================================================================

CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:3000',
    'http://127.0.0.1:3000',
])
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-requested-with',
]
CORS_EXPOSE_HEADERS = [
    'X-Request-ID',
    'X-RateLimit-Remaining',
    'Retry-After',
]
CORS_ALLOW_METHODS = [
    'GET',
    'OPTIONS',
    'POST',               # GraphQL mutations
]

# =============================================================================
# SESSION & COOKIE SECURITY
# =============================================================================

# Use Redis for sessions (consistent with cache layer)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'
SESSION_COOKIE_NAME = '__nova_sid'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 1800          # 30 minutes
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True  # rolling expiry

# CSRF cookie (used only for Django admin; GraphQL uses JWT)
CSRF_COOKIE_NAME = '__nova_csrf'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_AGE = 3600            # 1 hour
CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'

# =============================================================================
# FILE UPLOAD SETTINGS
# =============================================================================

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

ALLOWED_UPLOAD_EXTENSIONS = {
    'ebook': ['.pdf', '.epub'],
    'audiobook': ['.mp3', '.m4a', '.ogg', '.wav'],
    'image': ['.jpg', '.jpeg', '.png', '.webp'],
    'id_document': ['.jpg', '.jpeg', '.png', '.pdf'],
}

MAX_UPLOAD_SIZES = {
    'ebook': 100 * 1024 * 1024,      # 100MB
    'audiobook': 500 * 1024 * 1024,   # 500MB
    'image': 5 * 1024 * 1024,         # 5MB
    'id_document': 10 * 1024 * 1024,  # 10MB
}

# =============================================================================
# STORAGE BACKEND
# =============================================================================

FILE_STORAGE_BACKEND = env('FILE_STORAGE_BACKEND', default='local')

# S3 Configuration (when FILE_STORAGE_BACKEND='s3')
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', default='')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME', default='')
AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='us-east-1')
AWS_DEFAULT_ACL = 'private'
AWS_S3_FILE_OVERWRITE = False

# =============================================================================
# AI CONFIGURATION
# =============================================================================

AI_CONFIG = {
    'EMBEDDING_MODEL': env('EMBEDDING_MODEL_NAME', default='all-MiniLM-L6-v2'),
    'EMBEDDING_DIMENSION': 384,
    'FACE_RECOGNITION_TOLERANCE': float(env('FACE_RECOGNITION_TOLERANCE', default=0.6)),
    'OCR_LANGUAGE': env('OCR_LANGUAGE', default='eng'),
    'RECOMMENDATION_CACHE_TTL': int(env('RECOMMENDATION_CACHE_TTL', default=86400)),
    'POPULARITY_DECAY_LAMBDA': 0.005,
    'COLD_START_THRESHOLD': 5,  # Minimum interactions before personalized recs
    'VERIFICATION_AUTO_APPROVE_THRESHOLD': 0.75,
    'VERIFICATION_MANUAL_REVIEW_THRESHOLD': 0.50,
    # --- Search & NLP (Role 5) ---
    'SEARCH_FULLTEXT_WEIGHT': 0.45,
    'SEARCH_SEMANTIC_WEIGHT': 0.35,
    'SEARCH_FUZZY_WEIGHT': 0.20,
    'SEARCH_PERSONALISATION_BOOST': 0.15,
    'SEARCH_MIN_SCORE': 0.05,
    'AUTOSUGGEST_LIMIT': 8,
    # --- Predictive Analytics (Role 5) ---
    'OVERDUE_RISK_THRESHOLD': 0.6,
    'CHURN_RISK_THRESHOLD': 0.6,
    'CHURN_ANALYSIS_WEEKS': 8,
    'DEMAND_FORECAST_WEEKS': 12,
    'COLLECTION_GAP_MIN_SEVERITY': 'MODERATE',
    # --- Content Analysis (Role 5) ---
    'AUTO_TAG_TOP_N': 5,
    'DUPLICATE_TITLE_THRESHOLD': 0.85,
    'DUPLICATE_EMBEDDING_THRESHOLD': 0.92,
    'READING_LEVEL_DEFAULT': 'INTERMEDIATE',
    # --- Notifications (Role 5) ---
    'NOTIFICATION_DAILY_CAP': 8,
    'NOTIFICATION_DEDUP_HOURS': 2,
    'NOTIFICATION_CHANNELS': ['IN_APP', 'EMAIL'],
    # --- Training Pipeline (Role 5) ---
    'TRAINING_BATCH_SIZE': 200,
    'COLLABORATIVE_TOP_K_NEIGHBORS': 20,
    'COLLABORATIVE_MIN_SIMILARITY': 0.1,
    'MODEL_ARTIFACT_DIR': 'data/models',
}

# =============================================================================
# RATE LIMITING
# =============================================================================

RATE_LIMIT_CONFIG = {
    'DEFAULT': env('RATE_LIMIT_DEFAULT', default='100/hour'),
    'AUTH': env('RATE_LIMIT_AUTH', default='5/minute'),
    'MUTATION': '30/minute',
    'QUERY': '120/minute',
    'HEARTBEAT': '60/minute',
    'UPLOAD': env('RATE_LIMIT_UPLOAD', default='10/hour'),
}

# =============================================================================
# ACCOUNT SECURITY (brute-force / lockout)
# =============================================================================

ACCOUNT_SECURITY = {
    'MAX_FAILED_ATTEMPTS': int(env('ACCOUNT_MAX_FAILED_ATTEMPTS', default=5)),
    'LOCKOUT_BASE_SECONDS': 300,          # 5 minutes first lockout
    'LOCKOUT_MAX_SECONDS': 3600,          # 1 hour maximum lockout
    'LOCKOUT_MULTIPLIER': 2,              # exponential back-off factor
    'FAILED_ATTEMPT_WINDOW_SECONDS': 900, # 15-minute sliding window
    'IP_MAX_FAILED_ATTEMPTS': 20,
    'IP_LOCKOUT_SECONDS': 600,            # 10-minute IP-level lockout
}

# =============================================================================
# ENGAGEMENT CONFIGURATION
# =============================================================================

ENGAGEMENT_CONFIG = {
    'DAILY_KP_CAP': 200,
    'MIN_SESSION_DURATION_SECONDS': 120,  # 2 minutes minimum for KP
    'IDLE_THRESHOLD_SECONDS': 60,  # 60 seconds without heartbeat = idle
    'SESSION_TIMEOUT_SECONDS': 5400,  # 90 minutes max session
    'HEARTBEAT_INTERVAL_SECONDS': 30,
    'MAX_HEARTBEAT_GAP_SECONDS': 90,  # Auto-pause after 90 seconds
    'MIN_NOTE_LENGTH': 10,
    'MAX_NOTES_PER_ASSET': 100,
    'STREAK_MIN_ACTIVE_MINUTES': 15,
    'KP_WEIGHTS': {
        'READING_TIME': 0.30,
        'COMPLETION': 0.25,
        'CONTENT_CREATION': 0.20,
        'CONSISTENCY': 0.15,
        'DIVERSITY': 0.10,
    },
    'STREAK_MULTIPLIERS': {
        3: 1.1,
        7: 1.2,
        14: 1.3,
        30: 1.5,
    },
    'LEVELS': {
        1: {'min_kp': 0, 'title': 'Curious Reader'},
        2: {'min_kp': 100, 'title': 'Active Learner'},
        3: {'min_kp': 500, 'title': 'Knowledge Seeker'},
        4: {'min_kp': 1500, 'title': 'Scholar'},
        5: {'min_kp': 5000, 'title': 'Thought Leader'},
    },
}

# =============================================================================
# CIRCULATION CONFIGURATION
# =============================================================================

CIRCULATION_CONFIG = {
    'DEFAULT_BORROW_DAYS': 14,
    'MAX_EXTENSIONS': 2,
    'MAX_CONCURRENT_BORROWS': 2,            # Max active borrows per user
    'MAX_CONCURRENT_RESERVATIONS': 2,       # Max active reservations per user
    'RESERVATION_PICKUP_HOURS': 12,        # Hours to pick up a READY reservation
    'FINE_BASE_RATE_PER_DAY': 0.50,
    'FINE_ESCALATION_TIERS': {
        7: 1.0,    # Days 1-7: base rate × 1.0
        30: 1.5,   # Days 8-30: base rate × 1.5
        999: 2.0,  # Days 31+: base rate × 2.0
    },
    'MAX_UNPAID_FINE_THRESHOLD': 25.00,    # Block reserving above this
    'OVERDUE_REMINDER_DAYS': [3, 1, 0, -1, -3, -7],
    # Anti-abuse settings
    'ABUSE_LOOKBACK_DAYS': 30,             # Window to count no-shows
    'ABUSE_MAX_NO_SHOWS': 3,               # No-shows before ban
    'ABUSE_BAN_DAYS': 7,                   # Duration of reservation ban
}

# =============================================================================
# LOGGING – Defined per environment, base structure here
# =============================================================================

LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {name} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            '()': 'apps.common.logging_formatters.JSONFormatter',
        },
        'simple': {
            'format': '{asctime} {levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file_general': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'nova.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'error.log'),
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'json',
        },
        'file_security': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'security.log'),
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 30,
            'formatter': 'json',
        },
        'file_audit': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'audit.log'),
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 30,
            'formatter': 'json',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_general'],
            'level': 'INFO',
            'propagate': False,
        },
        'nova': {
            'handlers': ['console', 'file_general', 'file_error'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'nova.security': {
            'handlers': ['console', 'file_security'],
            'level': 'INFO',
            'propagate': False,
        },
        'nova.audit': {
            'handlers': ['file_audit'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file_general'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file_general'],
        'level': 'INFO',
    },
}
