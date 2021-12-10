#!/bin/sh
mkdir -p /tmp/rgd/https
python -m simple_httpfs /tmp/rgd/https
mkdir -p /tmp/rgd/http
python -m simple_httpfs /tmp/rgd/http
mkdir -p /tmp/rgd/s3
python -m simple_httpfs /tmp/rgd/s3
exec "$@"
