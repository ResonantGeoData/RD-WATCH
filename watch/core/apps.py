from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'watch.core'
    verbose_name = 'ResonantGeoData WATCH: Core'

    def ready(self):
        import watch.core.signals  # noqa: F401
