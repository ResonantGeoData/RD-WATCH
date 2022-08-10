# Deployment

This document gives an overview of how to deploy this web application.

## Quick start

A production-ready Docker Compose configuration is provided to easily deploy this application.

1. Make a copy of the file ["template.env"](https://github.com/ResonantGeoData/RD-WATCH/blob/phase-ii/template.env) as ".env" and fill it out
2. Update the Docker images: `docker compose pull`
3. Start the services: `docker compose up`
4. [optional] Run migrations: `docker compose run --rm poetry run django-admin migrate`

The web application is available on [http://localhost:8000](http://localhost:8000). It's recommended to run NGINX or use a CDN to proxy requests to the application in order to have HTTP/2 and SSL.

## Manual deployment

The application is provided as a single Docker image for both `x86_64` and `arm64`: [`ghcr.io/resonantgeodata/rd-watch/rdwatch`](https://github.com/resonantgeodata/RD-WATCH/pkgs/container/rd-watch%2Frdwatch). There is only one tag, `latest`, that tracks the head of the `phase-ii` branch. This image is configured via environment variables as described in ["template.env"](https://github.com/ResonantGeoData/RD-WATCH/blob/phase-ii/template.env). It runs a single process with multi-threading to serve requests via HTTP/1.1. The services that `RDWATCH_POSTGRESQL_URI` and `RDWATCH_REDIS_URI` point to should be:

- [PostgreSQL 14](https://www.postgresql.org/docs/14/index.html) with [PostGIS 3.2](http://www.postgis.net/documentation/)
- [Redis 7](https://redis.io/docs/)
