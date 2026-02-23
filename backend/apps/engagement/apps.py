from django.apps import AppConfig


class EngagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.engagement'
    verbose_name = 'Engagement & Gamification'

    def ready(self):
        import apps.engagement.infrastructure.signals  # noqa: F401
