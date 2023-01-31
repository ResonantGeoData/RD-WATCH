from os import environ
from urllib.parse import urlparse

SECRET_KEY = environ["RDWATCH_SECRET_KEY"]


ALLOWED_HOSTS = ["*"]
CACHES = {
    # TODO: Ideally we'd use Django's native Redis cache adapter instead of
    # the third-party `django-redis` package. But, the native adapter doesn't
    # seem to support cluster mode when using AWS Elasticache, while
    # `django-redis` does.
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "KEY_PREFIX": "rdwatch",
        "LOCATION": environ["RDWATCH_REDIS_URI"],
        "OPTIONS": {
            "REDIS_CLIENT_CLASS": "rediscluster.RedisCluster",
            "CONNECTION_POOL_CLASS": "rediscluster.connection.ClusterConnectionPool",  # noqa: E501
            "CONNECTION_POOL_KWARGS": {
                # AWS ElasticCache has disabled CONFIG commands
                "skip_full_coverage_check": True
            },
        },
    }
}
DATABASE_PARSE_RESULT = urlparse(environ["RDWATCH_POSTGRESQL_URI"])
DATABASES = {
    "default": {
        "CONN_MAX_AGE": None,
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "HOST": DATABASE_PARSE_RESULT.hostname,
        "NAME": DATABASE_PARSE_RESULT.path.strip("/"),
        "PASSWORD": DATABASE_PARSE_RESULT.password,
        "PORT": DATABASE_PARSE_RESULT.port,
        "USER": DATABASE_PARSE_RESULT.username,
        "TEST": {
            "NAME": "test_rdwatch",
        },
    },
}
DEBUG = environ["RDWATCH_DJANGO_DEBUG"].lower() in ("1", "true", "yes", "on")
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.gis",
    "django.contrib.postgres",
    "django_filters",
    "rest_framework",
    "rdwatch",
]
MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "rdwatch.middleware.Log500ErrorsMiddleware",
]
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
}
ROOT_URLCONF = "rdwatch.server.urls"
USE_I18N = False
USE_TZ = False
USE_X_FORWARDED_HOST = True
WSGI_APPLICATION = "rdwatch.server.application"
