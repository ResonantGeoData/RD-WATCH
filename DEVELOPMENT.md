# Development

This document gives an overview of the code contained in this monorepo and the recommended development setup.

## Develop with Docker (recommended quickstart)
This is the simplest configuration for developers to start with.

1. Make a copy of `template.env` and call it `.env`.
2. Set the environment variables in `.env`.
3. Run `docker compose up` to start the Django development server and Celery worker, plus all backing services
   like PostGIS, Redis, RabbitMQ, etc.
4. Start the client development server:
   ```sh
   cd vue
   npm install
   npm run dev
   ```
5. Access the site, starting at http://localhost:8080/
6. When finished, use `Ctrl+C`

## Develop Natively (advanced)
This configuration still uses Docker to run attached services in the background,
but allows developers to run Python code on their native system.

### Initial Setup
1. Run `cp dev/.env.template.private dev/.env.private`
2. Set the environment variables in `dev/.env.private`.
3. Run `docker compose -f ./docker-compose.yaml up -d`
4. Install Python 3.10
5. Install
   [`psycopg2` build prerequisites](https://www.psycopg.org/docs/install.html#build-prerequisites)
6. Install Poetry
7. Run `poetry install`
8. Run `source ./dev/export-env.sh`

### Run Application
1.  Ensure `docker compose -f ./docker-compose.yaml up -d` is still active
2. Run:
   1. `source ./dev/export-env.sh`
   2. `poetry run --directory django django-admin runserver`
3. Run in a separate terminal:
   1. `source ./dev/export-env.sh`
   2. `poetry run --directory django celery --app rdwatch.celery worker --loglevel INFO --without-heartbeat`
4. When finished, run `docker compose stop`
5. To destroy the stack and start fresh, run `docker compose down`
   1. Note: this command does not destroy docker volumes, such as those associated with the postgresql and minio services. To destroy those as well, run `docker compose down -v`.

## Type support for ".vue" imports in VS Code

Enable ["takeover mode"](https://github.com/johnsoncodehk/volar/discussions/471) for Volar.

1. Disable built-in TypeScript extension:
   1. Open the Command Palette (<kbd>⌘</kbd> <kbd>⇧</kbd> <kbd>P</kbd> or <kbd>Ctrl</kbd> <kbd>Shift</kbd> <kbd>P</kbd>) and run `>Extensions: Show Built-in Extensions` command
   2. Find "TypeScript and JavaScript Language Features", right click and select "Disable (Workspace)"
2. Reload VS Code

## Stack

The key software used to build the application.

### Django

A single Django application (`rdwatch`) for the backend. Source code is in the ["django"](https://github.com/ResonantGeoData/RD-WATCH/tree/phase-ii/django) folder.

- [Django 4](https://docs.djangoproject.com/en/4.1/contents/) with [GeoDjango](https://docs.djangoproject.com/en/4.0/ref/contrib/gis/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Poetry](https://python-poetry.org/docs/) for dependency management

### Vue

The Vue-based SPA frontend. Source code is in the ["vue"](https://github.com/ResonantGeoData/RD-WATCH/tree/phase-ii/vue) folder.

- [Vue 3](https://vuejs.org/guide/introduction.html)
- [TailwindCSS](https://tailwindcss.com/docs)
- [MapLibre GL JS](https://maplibre.org/maplibre-gl-js-docs/api/)
- [npm](https://docs.npmjs.com/) for dependency management

### Services

Services the application requires.

- [NGINX Unit](https://unit.nginx.org/): serves both the backend and the bundled static assets ([Dockerfile](https://github.com/ResonantGeoData/RD-WATCH/blob/phase-ii/Dockerfile))
- [PostgreSQL 14](https://www.postgresql.org/docs/14/index.html) and [PostGIS 3.2](http://www.postgis.net/documentation/): data warehouse ([Dockerfile](https://github.com/ResonantGeoData/RD-WATCH/blob/phase-ii/docker/services/postgresql/Dockerfile))
- [Redis 7](https://redis.io/docs/): caching (and maybe in the future as a job queue) ([Dockerfile](https://github.com/ResonantGeoData/RD-WATCH/blob/phase-ii/docker/services/redis/Dockerfile))
