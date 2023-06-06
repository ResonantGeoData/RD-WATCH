#!/bin/sh
set -e

export DJANGO_SETTINGS_MODULE=rdwatch.server.settings

# Tail Django logs
touch /tmp/django.log
chmod a+w /tmp/django.log
nohup tail -f /tmp/django.log &

# Initialize NGINX Unit
if [ "$1" = "unitd" ]; then
  if [ ! -f /var/lib/unit/conf.json ]; then
    unitd --control unix:/run/control.unit.sock
    while [ ! -S /run/control.unit.sock ]; do sleep 0.1; done
    curl -s -X PUT \
      --data @/usr/local/etc/unit/config.json \
      --unix-socket /run/control.unit.sock \
      http://localhost/config/ > /dev/null
    kill -TERM `cat /run/unit.pid`
  fi
fi

poetry run --directory /app/django /app/django/src/manage.py migrate
poetry run --directory /app/django /app/django/src/manage.py loaddata lookups

exec "$@"
