"""
Nova — Celery Application Configuration
=========================================
Configures Celery for background task processing.
"""

import os

from celery import Celery
from celery.signals import setup_logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nova.settings.development')

app = Celery('nova')

# Load config from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()


@setup_logging.connect
def config_loggers(*args, **kwargs):
    """Use Django's logging configuration for Celery."""
    from logging.config import dictConfig
    from django.conf import settings
    dictConfig(settings.LOGGING)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery connectivity."""
    print(f'Request: {self.request!r}')
