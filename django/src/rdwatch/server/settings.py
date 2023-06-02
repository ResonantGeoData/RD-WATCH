import os

from configurations import Configuration, values

_environ_prefix = 'RDWATCH'


# With the default "late_binding=False", and "environ_name" is
# specified or "environ=False", even Values from non-included
# classes (e.g. `AWS_DEFAULT_REGION) get immediately evaluated and
# expect env vars to be set.
values.Value.late_binding = True


class BaseConfiguration(Configuration):
    ROOT_URLCONF = 'rdwatch.server.urls'
    USE_I18N = False
    USE_TZ = False
    USE_X_FORWARDED_HOST = True
    WSGI_APPLICATION = 'rdwatch.server.application'
    ALLOWED_HOSTS = ['*']
    DEBUG = values.BooleanValue(False, _environ_prefix='RDWATCH_DJANGO')

    INSTALLED_APPS = [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.gis',
        'django.contrib.postgres',
        'django_filters',
        'rest_framework',
        'django_extensions',
        'rdwatch',
        'django_celery_results',
    ]

    MIDDLEWARE = [
        'django.middleware.common.CommonMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'rdwatch.middleware.Log500ErrorsMiddleware',
    ]

    REST_FRAMEWORK = {
        'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
        'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser'],
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
        'PAGE_SIZE': 25,
    }

    NINJA_PAGINATION_CLASS = 'ninja.pagination.PageNumberPagination'

    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.environ['RDWATCH_REDIS_URI'],
            'OPTIONS': {
                'CLIENT_CLASS': 'rdwatch.redis.CustomRedisCluster',
            },
        }
    }

    CELERY_BROKER_URL = values.Value(
        environ_required=True,
        environ_prefix=_environ_prefix,
    )

    DATABASES = values.DatabaseURLValue(
        environ_name='POSTGRESQL_URI',
        environ_prefix=_environ_prefix,
        environ_required=True,
        # Additional kwargs to DatabaseURLValue are passed to dj-database-url
        engine='django.contrib.gis.db.backends.postgis',
        conn_max_age=None,
    )

    # Set to same value allowed by NGINX Unit server in `settings.http.max_body_size`
    # (in /docker/nginx.json)
    DATA_UPLOAD_MAX_MEMORY_SIZE = 134217728

    ACCENTURE_VERSION = values.Value(
        environ_required=True, environ_prefix=_environ_prefix
    )

    SMART_STAC_URL = values.URLValue(
        environ_required=True, environ_prefix=_environ_prefix
    )
    SMART_STAC_KEY = values.SecretValue(
        environ_required=True, environ_prefix=_environ_prefix
    )

    # django-celery-results configuration
    CELERY_RESULT_BACKEND = 'django-db'
    CELERY_CACHE_BACKEND = 'django-cache'
    CELERY_RESULT_EXTENDED = True
    CELERYD_TIME_LIMIT = 1200


class DevelopmentConfiguration(BaseConfiguration):
    SECRET_KEY = 'secretkey'  # Dummy value for local development configuration

    DEFAULT_FILE_STORAGE = 'minio_storage.storage.MinioMediaStorage'
    MINIO_STORAGE_ENDPOINT = values.Value(
        'localhost:9000', environ_prefix=_environ_prefix
    )
    MINIO_STORAGE_USE_HTTPS = values.BooleanValue(False, environ_prefix=_environ_prefix)
    MINIO_STORAGE_ACCESS_KEY = values.SecretValue(environ_prefix=_environ_prefix)
    MINIO_STORAGE_SECRET_KEY = values.SecretValue(environ_prefix=_environ_prefix)
    MINIO_STORAGE_MEDIA_BUCKET_NAME = values.Value(
        environ_prefix=_environ_prefix,
        environ_name='STORAGE_BUCKET_NAME',
        environ_required=True,
    )
    MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET = True
    MINIO_STORAGE_AUTO_CREATE_MEDIA_POLICY = 'READ_WRITE'
    MINIO_STORAGE_MEDIA_USE_PRESIGNED = True
    MINIO_STORAGE_MEDIA_URL = 'http://127.0.0.1:9000/rdwatch'


class ProductionConfiguration(BaseConfiguration):
    SECRET_KEY = values.Value(environ_required=True, environ_prefix=_environ_prefix)

    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

    AWS_STORAGE_BUCKET_NAME = values.Value(
        environ_prefix=_environ_prefix,
        environ_name='STORAGE_BUCKET_NAME',
        environ_required=True,
    )

    # It's critical to use the v4 signature;
    # it isn't the upstream default only for backwards compatability reasons.
    AWS_S3_SIGNATURE_VERSION = 's3v4'

    AWS_S3_MAX_MEMORY_SIZE = 5 * 1024 * 1024
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_EXPIRE = 3600 * 6  # 6 hours
