from os import environ
from urllib.parse import urlparse

SECRET_KEY = environ['RDWATCH_SECRET_KEY']


ALLOWED_HOSTS = ['*']
DEBUG = environ['RDWATCH_DJANGO_DEBUG'].lower() in ('1', 'true', 'yes', 'on')

if DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'KEY_PREFIX': 'rdwatch',
            'LOCATION': environ['RDWATCH_REDIS_URI'],
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': environ['RDWATCH_REDIS_URI'],
            'OPTIONS': {
                'CLIENT_CLASS': 'rdwatch.redis.CustomRedisCluster',
            },
        }
    }
DATABASE_PARSE_RESULT = urlparse(environ['RDWATCH_POSTGRESQL_URI'])
DATABASES = {
    'default': {
        'CONN_MAX_AGE': None,
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'HOST': DATABASE_PARSE_RESULT.hostname,
        'NAME': DATABASE_PARSE_RESULT.path.strip('/'),
        'PASSWORD': DATABASE_PARSE_RESULT.password,
        'PORT': DATABASE_PARSE_RESULT.port,
        'USER': DATABASE_PARSE_RESULT.username,
        'TEST': {
            'NAME': 'test_rdwatch',
        },
    },
}
CELERY_BROKER_URL = environ['RDWATCH_REDIS_URI']
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.gis',
    'django.contrib.postgres',
    'django_filters',
    'rest_framework',
    'django_extensions',
    'rdwatch',
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
ROOT_URLCONF = 'rdwatch.server.urls'
USE_I18N = False
USE_TZ = False
USE_X_FORWARDED_HOST = True
WSGI_APPLICATION = 'rdwatch.server.application'

ACCENTURE_IMAGERY_VERSION = environ.get('RDWATCH_ACCENTURE_VERSION', None)
