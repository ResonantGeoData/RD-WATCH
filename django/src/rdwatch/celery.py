import os

from celery import Celery

os.environ['DJANGO_SETTINGS_MODULE'] = 'rdwatch.server.settings'

# Using a string config_source means the worker doesn't have to serialize
# the configuration object to child processes.
app = Celery(config_source='django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
