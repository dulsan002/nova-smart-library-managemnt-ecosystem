from django.apps import AppConfig


class IdentityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.identity'
    verbose_name = 'Identity & Access Management'

    def ready(self):
        """Register signal handlers and event subscriptions."""
        import apps.identity.infrastructure.signals  # noqa: F401
