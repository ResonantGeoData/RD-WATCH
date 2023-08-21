import os
from datetime import timedelta

from configurations import Configuration, values

_ENVIRON_PREFIX = 'RDWATCH'

if os.name == 'nt':
    OSGEO4W = r"C:\OSGeo4W"
    assert os.path.isdir(OSGEO4W), "Directory does not exist: " + OSGEO4W
    os.environ['OSGEO4W_ROOT'] = OSGEO4W
    os.environ['GDAL_DATA'] = OSGEO4W + r"\share\gdal"
    os.environ['PATH'] = OSGEO4W + r"\bin;" + os.environ['PATH']


# With the default "late_binding=False", and "environ_name" is
# specified or "environ=False", even Values from non-included
# classes (e.g. `AWS_DEFAULT_REGION) get immediately evaluated and
# expect env vars to be set.
values.Value.late_binding = True

import os
if os.name == 'nt':
    OSGEO4W = r"C:\OSGeo4W"
    assert os.path.isdir(OSGEO4W), "Directory does not exist: " + OSGEO4W
    os.environ['OSGEO4W_ROOT'] = OSGEO4W
    os.environ['GDAL_DATA'] = OSGEO4W + r"\share\gdal"
    #os.environ['PROJ_LIB'] = OSGEO4W + r"\share\proj" //geoDjango PROJ_LIB conflicts
    os.environ['PATH'] = OSGEO4W + r"\bin;" + os.environ['PATH']

class BaseConfiguration(Configuration):
    ROOT_URLCONF = 'rdwatch.server.urls'
    USE_I18N = False
    USE_TZ = False
    USE_X_FORWARDED_HOST = True
    WSGI_APPLICATION = 'rdwatch.server.application'
    ALLOWED_HOSTS = ['*']
    DEBUG = values.BooleanValue(False, environ_prefix='RDWATCH_DJANGO')
    # Django's docs suggest that STATIC_URL should be a relative path,
    # for convenience serving a site on a subpath.
    STATIC_URL = 'static/'

    @property
    def INSTALLED_APPS(self):
        base_applications = [
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'django.contrib.gis',
            'django.contrib.postgres',
            'django_filters',
            'rest_framework',
            'django_extensions',
            'rdwatch',
            'django_celery_results',
        ]
        if 'RDWATCH_POSTGRESQL_SCORING_URI' in os.environ:
            base_applications.append('rdwatch_scoring')
        return base_applications

    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'rdwatch.middleware.Log500ErrorsMiddleware',
    ]

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        },
    ]

    @property
    def DATABASES(self):
        DB_val = values.DatabaseURLValue(
            alias='default',
            environ_name='POSTGRESQL_URI',
            environ_prefix=_ENVIRON_PREFIX,
            environ_required=True,
            # Additional kwargs to DatabaseURLValue are passed to dj-database-url
            engine='django.contrib.gis.db.backends.postgis',
        )
        db_dict = DB_val.value
        if 'RDWATCH_POSTGRESQL_SCORING_URI' in os.environ:
            scoring_val = values.DatabaseURLValue(
                alias='scoringdb',
                environ_name='POSTGRESQL_SCORING_URI',
                environ_prefix=_ENVIRON_PREFIX,
                environ_required=True,
                # Additional kwargs to DatabaseURLValue are passed to dj-database-url
                engine='django.contrib.gis.db.backends.postgis',
            )
            scoring_dict = scoring_val.value
            db_dict.update(scoring_dict)
        return db_dict

    REST_FRAMEWORK = {
        'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
        'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser'],
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
        'PAGE_SIZE': 25,
    }

    NINJA_PAGINATION_CLASS = 'ninja.pagination.PageNumberPagination'

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'KEY_PREFIX': 'rdwatch',
            'LOCATION': os.environ['RDWATCH_REDIS_URI'],
        }
    }

    CELERY_BROKER_URL = values.Value(
        environ_required=True,
        environ_prefix=_ENVIRON_PREFIX,
    )

    # Set to same value allowed by NGINX Unit server in `settings.http.max_body_size`
    # (in /docker/nginx.json)
    DATA_UPLOAD_MAX_MEMORY_SIZE = 134217728

    ACCENTURE_VERSION = values.Value(
        environ_required=True, environ_prefix=_ENVIRON_PREFIX
    )

    SMART_STAC_URL = values.URLValue(
        environ_required=True, environ_prefix=_ENVIRON_PREFIX
    )
    SMART_STAC_KEY = values.SecretValue(
        environ_required=True, environ_prefix=_ENVIRON_PREFIX
    )

    # django-celery-results configuration
    CELERY_RESULT_BACKEND = 'django-db'
    CELERY_CACHE_BACKEND = 'django-cache'
    CELERY_RESULT_EXTENDED = True
    CELERYD_TIME_LIMIT = 1200

    @property
    def DATABASE_ROUTERS(self):
        if 'RDWATCH_POSTGRESQL_SCORING_URI' in os.environ:
            return ['rdwatch_scoring.router.ScoringRouter']
        else:
            return []

    CELERY_BEAT_SCHEDULE = {
        'delete-temp-model-runs-beat': {
            'task': 'rdwatch.tasks.delete_temp_model_runs_task',
            'schedule': timedelta(hours=1),
        },
    }


class DevelopmentConfiguration(BaseConfiguration):
    SECRET_KEY = 'secretkey'  # Dummy value for local development configuration

    DEFAULT_FILE_STORAGE = 'minio_storage.storage.MinioMediaStorage'
    MINIO_STORAGE_ENDPOINT = values.Value(
        'localhost:9000', environ_prefix=_ENVIRON_PREFIX
    )
    MINIO_STORAGE_USE_HTTPS = values.BooleanValue(False, environ_prefix=_ENVIRON_PREFIX)
    MINIO_STORAGE_ACCESS_KEY = values.SecretValue(environ_prefix=_ENVIRON_PREFIX)
    MINIO_STORAGE_SECRET_KEY = values.SecretValue(environ_prefix=_ENVIRON_PREFIX)
    MINIO_STORAGE_MEDIA_BUCKET_NAME = values.Value(
        environ_prefix=_ENVIRON_PREFIX,
        environ_name='STORAGE_BUCKET_NAME',
        environ_required=True,
    )
    MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET = True
    MINIO_STORAGE_AUTO_CREATE_MEDIA_POLICY = 'READ_WRITE'
    MINIO_STORAGE_MEDIA_USE_PRESIGNED = True
    MINIO_STORAGE_MEDIA_URL = 'http://127.0.0.1:9000/rdwatch'


class ProductionConfiguration(BaseConfiguration):
    SECRET_KEY = values.Value(environ_required=True, environ_prefix=_ENVIRON_PREFIX)

    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

    AWS_STORAGE_BUCKET_NAME = values.Value(
        environ_prefix=_ENVIRON_PREFIX,
        environ_name='STORAGE_BUCKET_NAME',
        environ_required=True,
    )

    # It's critical to use the v4 signature;
    # it isn't the upstream default only for backwards compatability reasons.
    AWS_S3_SIGNATURE_VERSION = 's3v4'

    AWS_S3_MAX_MEMORY_SIZE = 5 * 1024 * 1024
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_EXPIRE = 3600 * 6  # 6 hours
