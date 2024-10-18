import logging
from typing import Literal, TypeAlias

from django.contrib.auth.models import User
from django.db.models import Model

DbName: TypeAlias = Literal['default', 'scoringdb']

# (app name, model object name) -> db name
# (app name, '*') is the fallback key for a given app
DB_ROUTES: dict[tuple[str, str], str] = {
    ('scoring', 'SiteImage'): 'default',
    ('scoring', 'SatelliteFetching'): 'default',
    ('scoring', 'AnimationSiteExport'): 'default',
    ('scoring', 'AnimationModelRunExport'): 'default',
    ('scoring', '*'): 'scoringdb',
}

logger = logging.getLogger(__name__)


class ScoringRouter:
    """
    A router to control all database operations on models in the
    auth and contenttypes applications.
    """

    route_app_labels = {'rdwatch.core', 'scoring'}

    def db_for_read(self, model: type[Model], **hints) -> DbName:
        """
        Route database reads.
        """
        app_label = model._meta.app_label
        object_name = model._meta.object_name
        return DB_ROUTES.get(
            (app_label, object_name), DB_ROUTES.get((app_label, '*'), 'default')
        )

    def db_for_write(self, model: type[Model], **hints) -> DbName | None:
        """
        Route database writes.
        """
        app_label = model._meta.app_label
        object_name = model._meta.object_name
        return DB_ROUTES.get(
            (app_label, object_name), DB_ROUTES.get((app_label, '*'), 'default')
        )

    def allow_relation(
        self, obj1: type[Model], obj2: type[Model], **hints
    ) -> bool | None:
        """
        Allow relations if a model is all core or all scoring/
        """
        labels = {obj1._meta.app_label, obj2._meta.app_label}
        if 'core' in labels and 'scoring' in labels:
            return False
        if obj1._meta.app_label == 'auth' and isinstance(obj1, User):
            return True
        if obj2._meta.app_label == 'auth' and isinstance(obj2, User):
            return True
        return None

    def allow_migrate(
        self, db: str, app_label: str, model_name=None, **hints
    ) -> bool | None:
        if db == 'scoringdb':
            return False
        elif app_label in self.route_app_labels:
            return db == 'default'
        return None
