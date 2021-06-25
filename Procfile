release: ./manage.py migrate
web: gunicorn --bind 0.0.0.0:$PORT watch.wsgi
worker: REMAP_SIGTERM=SIGQUIT celery --app watch.celery worker --loglevel INFO --without-heartbeat
