"""
Nova — Intelligence App Configuration
"""

from django.apps import AppConfig


class IntelligenceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.intelligence'
    verbose_name = 'Intelligence & AI'

    def ready(self):
        import apps.intelligence.infrastructure.signals  # noqa: F401
