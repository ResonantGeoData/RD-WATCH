# Development

This document gives an overview of the code contained in this monorepo and the recommended development setup.

## Develop with Docker (recommended quickstart)
This is the simplest configuration for developers to start with.

1. Make a copy of `template.env` and call it `.env`.
2. Set the environment variables in `.env`.
3. Run `docker compose up` to start the Django development server and Celery worker, plus all backing services
   like PostGIS, Redis, RabbitMQ, etc.
4. Run `docker compose run --rm django poetry run django-admin migrate` to apply database migrations.
5. Run `docker compose run --rm django poetry run django-admin loaddata lookups` to initialize your database with required data.
6. Optionally, populate your database with test data by running `docker compose run --rm django poetry run django-admin loaddata testdata`
7. Optionally, create an account for the Django admin (http://localhost:8000/admin) by running `docker compose run --rm django poetry --directory django run django-admin createsuperuser`
8. Start the client development server:
   ```sh
   cd vue
   npm install
   npm run dev
   ```
9. Access the site, starting at http://localhost:8080/
10. When finished, use `Ctrl+C`

## Develop Natively (advanced)
This configuration still uses Docker to run attached services in the background,
but allows developers to run Python code on their native system.

### Initial Setup
1. Make a copy of `template.env` and call it `.env`.
2. Set the environment variables in `.env`.
3. Run `docker compose -f ./docker-compose.yaml up -d`
4. Install Python 3.11
5. Install
   [`psycopg2` build prerequisites](https://www.psycopg.org/docs/install.html#build-prerequisites)
6. Install Poetry
7. Run `poetry --directory django install`
8. Run the following command to configure your environment: `source ./dev/export-env.sh dev/.env.docker-compose-native ./dev/export-env.sh .env`
9. Optionally, populate your database with test data by running `poetry --directory django run django-admin loaddata testdata`
10. Optionally, create an account for the Django admin (http://localhost:8000/admin) by running `poetry --directory django run django-admin createsuperuser`

### Run Application
1. Ensure `docker compose -f ./docker-compose.yaml up -d` is still active
2. Run:
   1. `source ./dev/export-env.sh dev/.env.docker-compose-native`
   2. `source ./dev/export-env.sh .env`
   3. `poetry run --directory django django/src/manage.py migrate`
   4. `poetry run --directory django django/src/manage.py loaddata lookups`
   5. `poetry run --directory django django/src/manage.py runserver`
3. Run in a separate terminal:
   1. `source ./dev/export-env.sh`
   2. `poetry run --directory django celery --app rdwatch.celery worker --loglevel INFO --without-heartbeat`
4. Run in another separate terminal:
   1. `source ./dev/export-env.sh`
   2. `poetry run --directory django celery --app rdwatch.celery beat --loglevel INFO`
5. When finished, run `docker compose stop`
6. To destroy the stack and start fresh, run `docker compose down`
   1. Note: this command does not destroy docker volumes, such as those associated with the postgresql and minio services. To destroy those as well, run `docker compose down -v`.

### A note on database migrations
Note that database migrations are _not_ run automatically. Anytime a new migration is introduced, you must run the following command to apply it:

`poetry --directory django run django-admin migrate`

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
- [Vuetify](https://vuetifyjs.com/en/)
- [MapLibre GL JS](https://maplibre.org/maplibre-gl-js-docs/api/)
- [npm](https://docs.npmjs.com/) for dependency management

### Services

Services the application requires.

- [NGINX Unit](https://unit.nginx.org/): serves both the backend and the bundled static assets ([Dockerfile](https://github.com/ResonantGeoData/RD-WATCH/blob/phase-ii/Dockerfile))
- [PostgreSQL 14](https://www.postgresql.org/docs/14/index.html) and [PostGIS 3.2](http://www.postgis.net/documentation/): data warehouse ([Dockerfile](https://github.com/ResonantGeoData/RD-WATCH/blob/phase-ii/docker/services/postgresql/Dockerfile))
- [Redis 7](https://redis.io/docs/): caching (and maybe in the future as a job queue) ([Dockerfile](https://github.com/ResonantGeoData/RD-WATCH/blob/phase-ii/docker/services/redis/Dockerfile))

### Ingesting Data

#### Loading Ground Truth Data

Within the ./scripts directory is a python script named `loadGroundTruth.py`.  This file can be used in conjunction with the ground truth annotaitons located in the annotation Repo:
[Annotation Repo](https://smartgitlab.com/TE/annotations)
Running a command like `python loadGroundTruth.py ~/AnnotationRepoLocation --skip_region` will load all of the annotations for the ground truth while skipping the regions.


#### Loading Single Model Runs
Within the ./scripts directory is a python script named `loadModelRuns.py`.  This can be used to load a folder filled with geojson data into the system by using a command like:

```
python loadModelRuns.py 'KR_0001' "./site_models/KR_R001_*.geojson" --title Test_Eval_12 --performer_shortcode 'KIT' --eval_num 12 --eval_run_num 0
```
Within this python file at the top is the rgd_endpoint variable which needs to be set to the server URL and port for where RGD is hosted.  By default this assumes running locally with `http://localhost:8000`
Be sure that the system is up and running before running the commands.
The above command will load the data in the site_models/KR_R001 files and give it the title 'Test_Eval_12'.  The eval_num and eval_run_num aren't required unless the scoring database is going to be connected to the system.  Within the script there is

### Scoring

The [Metrics and Test Framework](https://smartgitlab.com/TE/metrics-and-test-framework#creating-a-metrics-database) can be used in addition with RGD to display scores from results.
In development mode a scoring Database is automatically initialized at URI: `postgresql+psycopg2://scoring:secretkey@localhost:5433/scoring`

To score data:
- Begin by first starting the the score DB using `docker compose up scoredb`
- After that in the Metrics and Test Framework, copy the `alembic_example.ini` to `alembic.ini` and set the `sqlalchemy.url = postgresql+psycopg2://scoring:secretkey@localhost:5433/scoring`
- install the scoring code `pip install -e .` from the root of the Metrics and Test Framework Repository
- run `alembic upgrade head` to make sure the database is configured properly to load results.
    - Instead of running the above command you can run the following command from inside the RD-WATCH repository `docker compose run --rm django poetry run django-admin migrate rdwatch_scoring --database scoringdb` this will use the django migrations to initialize the database.
- Execute the scoring code from inside the mtrics and test framework:
```
  python -m iarpa_smart_metrics.run_evaluation \
               --roi KR_R001 \
               --gt_dir ../annotations/site_models/ \
               --rm_dir ../KR_R001/region_models/ \
               --sm_dir ../KR_R001/site_models/ \
               --output_dir ../KR_R001/output \
               --eval_num 12 \
               --eval_run_num 0 \
               --performer kit \
               --no-viz \
               --no-viz-detection-table \
               --no-viz-comparison-table \
               --no-viz-associate-metrics \
               --no-viz-activity-metrics \
               --sequestered_id KR_R001 \
               --db_conn_str postgresql+psycopg2://scoring:secretkey@localhost:5433/scoring
```
- the rm_dir and sm_dir shgould be your test annotaitons.
- gt annotations can be retrieved from the [Annotation Repo](https://smartgitlab.com/TE/annotations)
- be sure to set the val_num and eval_run_num and remember them when ingesting data into RGD.  The region, eval_num, eval_run_num and performer are used to connect data loaded in RGD to the scoring data.
