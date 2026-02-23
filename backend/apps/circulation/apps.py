from django.apps import AppConfig


class CirculationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.circulation'
    verbose_name = 'Circulation & Borrowing'

    def ready(self):
        import apps.circulation.infrastructure.signals  # noqa: F401
