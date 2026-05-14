from django.apps import AppConfig


class AtivosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ativos'

    def ready(self):
        import ativos.signals  # noqa: F401

class TelemetriaConfig(AppConfig):
    name = 'telemetria'
    def ready(self):
        import telemetria.signals  # noqa: F401