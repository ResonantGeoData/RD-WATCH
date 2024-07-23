# Architecture

## Overview

The basic RDWATCH systems is based on utilizing docker containers to create a full contained application for local development and deployment.

- Django is used as the back-end ORM with Postgres/PostGIS as a database.  There are multiple Django apps.  One for base RDWATCH and one for the Scoring data.
- Celery is used to execute and manage long running tasks.
- MinIO/S3 is used as object storage for cropped/chipped satellite images.
- Vue based front-end utilizing Vuetify for components and Maplibre for vector tile rendering

## Django Overview

### Core

This is the base application for RDWATCH.  All endpoints that don't contain `api/v1/scoring/*` will utilize the base Core Application.
This is also the mode location for all satellite image storage and downloading progress.

### Scoring

When the Environment Variable `RDWATCH_POSTGRESQL_SCORING_URI` is set the system expects to be connected to a second Database.  This database is based of the T&E metrics scoring database.  The RDWATCH team doesn't have direct control over the schema of this database so any data that is modified or stored should be placed in the RDWATCH database (This includes data like Stored Satellite Images or downloading progress).

For reading from the database Django Models are created but the `managed` property in the `Meta` class is set to False.  This allows for reading from the database using similar django querysets and orm logic while not having django actively manage the system.  This means that when the DB changes the models need to be updated.

The standard `rdwatch/core/views` endpoints for visualizing model-runs, sites, siteobservations are all mirrored in the Scoring application so they can access information directly from the scoring database.

### Tasks

Each app **core** and **scoring** has it's own tasks used in celery.  These are tasks that will download GeoJSON for an entire model run as well as downloading satellite images.  All information regarding satellite images are stored in the core rdwatch database because this project doesn't have access to modify the **scoring** database.

## Stack Links

### Django

A single Django application (`rdwatch`) for the backend. Source code is in the ["rdatch"](https://github.com/ResonantGeoData/RD-WATCH/tree/main/rdwatch) folder.

- [Django 4](https://docs.djangoproject.com/en/4.1/contents/) with [GeoDjango](https://docs.djangoproject.com/en/4.0/ref/contrib/gis/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Django Ninja](https://django-ninja.dev/)
- [Poetry](https://python-poetry.org/docs/) for dependency management

### Vue

The Vue-based SPA frontend. Source code is in the ["vue"](https://github.com/ResonantGeoData/RD-WATCH/tree/phase-ii/vue) folder.

- [Vue 3](https://vuejs.org/guide/introduction.html)
- [Vuetify](https://vuetifyjs.com/en/)
- [MapLibre GL JS](https://maplibre.org/maplibre-gl-js-docs/api/)
- [npm](https://docs.npmjs.com/) for dependency management

### Services

Services the application requires.

- [NGINX Unit](https://unit.nginx.org/): serves both the backend and the bundled static assets
- [PostgreSQL 14](https://www.postgresql.org/docs/14/index.html) and [PostGIS 3.2](http://www.postgis.net/documentation/): data warehouse for the RDWATCH database
- [Redis 7](https://redis.io/docs/): caching (and maybe in the future as a job queue)
- [MinIO/S3](https://min.io/): storage for satellite images for faster browsing
- [Celery](https://min.io/): long running tasks for image chipping, downloading and compressing geoJSONs.
