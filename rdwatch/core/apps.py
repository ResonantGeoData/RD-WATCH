import logging
import re

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from django.apps import AppConfig
from django.conf import settings


class RDWatchConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'rdwatch.core'

    @staticmethod
    def _get_sentry_trace_sample_rate(*args, **kwargs) -> float:
        # Routes that should have a 100% trace rate.
        # All other routes will have a 5% trace rate.
        priority_routes = [
            r'^/api/scoring/model-runs/[^/]+/sites/$',
        ]

        if len(args) and 'wsgi_environ' in args[0]:
            wsgi_environ = args[0]['wsgi_environ']

            url_path = wsgi_environ.get('PATH_INFO')

            for regex in priority_routes:
                if re.match(regex, url_path):
                    return 1.0

        return 0.05

    def ready(self) -> None:
        if hasattr(settings, 'SENTRY_DSN'):
            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                environment=settings.SENTRY_ENVIRONMENT,
                release=settings.SENTRY_RELEASE,
                integrations=[
                    LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
                    DjangoIntegration(),
                    CeleryIntegration(),
                ],
                # Only include rdwatch/ in the default stack trace
                in_app_include=['rdwatch'],
                # Send traces for non-exception events too
                attach_stacktrace=True,
                # Submit request User info from Django
                send_default_pii=True,
                traces_sampler=self._get_sentry_trace_sample_rate,
                profiles_sample_rate=1.0,
            )
        return super().ready()
