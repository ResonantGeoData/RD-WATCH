# Development

This document gives an overview of the code contained in this monorepo and the recommended development setup.

## Quick start

Get up and running with the recommended development setup. It's advised to develop in the provided container since we depend on some system dependencies (e.g. GDAL).

1. Make a copy of the file ["template.env"](https://github.com/ResonantGeoData/RD-WATCH/blob/phase-ii/template.env) as ".env" and fill it out
2. Pull in the Docker images: `docker compose --profile vscode pull`
3. Install the dependencies for Django: `docker compose run --rm poetry install`
4. Install the dependencies for Vue: `docker compose run --rm npm install`
5. Install the VS Code [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension
6. In VS Code, open the Command Palette (<kbd>⌘</kbd> <kbd>⇧</kbd> <kbd>P</kbd> or <kbd>Ctrl</kbd> <kbd>Shift</kbd> <kbd>P</kbd>) and run `>Remote-Containers: Open Workspace in Container...` selecting the file ["vscode.code-workspace"](https://github.com/ResonantGeoData/RD-WATCH/blob/phase-ii/vscode.code-workspace) as the Workspace file

Two ports will be open:

- [localhost:8000](localhost:8000): the latest version of the application on the `phase-ii` branch
- [localhost:9000](localhost:9000): live updating application (server reload for Django and HMR for Vue)

### Common tasks

- [`django-admin`](https://docs.djangoproject.com/en/4.1/ref/django-admin) commands:
  - e.g. run migrations: `docker compose run --rm poetry run django-admin migrate`
  - e.g. load fixtures: `docker compose run --rm poetry run django-admin loaddata lookups`
  - e.g. run tests: `docker compose run --rm poetry run django-admin test`
- `npm` commands and scripts (see [`scripts` in `package.json`](https://github.com/ResonantGeoData/RD-WATCH/blob/phase-ii/vue/package.json#L5)):
  - e.g. lint and fix code: `docker compose run --rm npm run lint:fix`
  - e.g. run tests: `docker compose run --rm npm run test`
  - e.g. install a package: `docker compose run --rm npm install some-pacakge`
- `poetry` commands and tasks (see [`tasks` in `pyproject.toml`](https://github.com/ResonantGeoData/RD-WATCH/blob/phase-ii/django/pyproject.toml#L42)):
  - e.g. lint and fix code: `docker compose run --rm poetry run task lint:fix`
  - e.g. build the OpenAPI spec: `docker compose run --rm poetry run task build:openapi`
  - e.g. install a package: `docker compose run --rm poetry add some-pacakge`

### Type support for ".vue" imports in VS Code

Enable ["takeover mode"](https://github.com/johnsoncodehk/volar/discussions/471) for Volar.

1. Disable built-in TypeScript extension:
   1. Open the Command Palette (<kbd>⌘</kbd> <kbd>⇧</kbd> <kbd>P</kbd> or <kbd>Ctrl</kbd> <kbd>Shift</kbd> <kbd>P</kbd>) and run `>Extensions: Show Built-in Extensions` command
   2. Find "TypeScript and JavaScript Language Features", right click and select "Disable (Workspace)"
2. Reload VS Code

### Customization

- ["docker-compose.override.yaml"](https://docs.docker.com/compose/extends/) is .gitignored, so feel free to use it to modify your environment while testing.
- "django/requirements.dev.txt" is .gitignored to keep track of extra development dependencies you may like (e.g. [IPython](https://ipython.org/)). Install them with `docker compose run --rm poetry run pip install -r django-admin requirements.dev.txt`.
- ".vscode" directories are .gitignored. This way, you can modify the base recommended VS Code Workspace with any modifications you may like.

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
