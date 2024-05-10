# This project module is imported for us when Django starts. To ensure that Celery app
# is always defined prior to any shared_task definitions (so those tasks will bind to
# the app), import the Celery module here for side effects.
from .celery import app as _celery_app  # noqa: F401

# placeholder for version number, will be replaced by
# poetry-dynamic-versioning in production
__version__ = '0.0.0dev0'
