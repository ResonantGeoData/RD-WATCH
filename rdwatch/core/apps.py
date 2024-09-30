import logging

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from django.apps import AppConfig
from django.conf import settings


class RDWatchConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'rdwatch.core'

    def ready(self) -> None:
        if hasattr(settings, 'SENTRY_DSN'):
            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                environment=settings.SENTRY_ENVIRONMENT,
                release=settings.SENTRY_RELEASE,
                integrations=[
                    LoggingIntegration(level=logging.INFO, event_level=logging.WARNING),
                    DjangoIntegration(),
                    CeleryIntegration(),
                ],
                # Only include rdwatch/ in the default stack trace
                in_app_include=['rdwatch'],
                # Send traces for non-exception events too
                attach_stacktrace=True,
                # Submit request User info from Django
                send_default_pii=True,
                traces_sampler=0.01,
                profiles_sampler=0.01,
            )
        return super().ready()
