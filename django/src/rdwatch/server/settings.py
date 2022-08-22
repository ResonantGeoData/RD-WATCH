from os import environ
from urllib.parse import urlparse

SECRET_KEY = environ["RDWATCH_SECRET_KEY"]


ALLOWED_HOSTS = ["*"]
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "KEY_PREFIX": "rdwatch",
        "LOCATION": environ["RDWATCH_REDIS_URI"],
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
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.humanize",
    "django.contrib.postgres",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "rest_framework",
    "rdwatch",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
STATIC_URL = "static/"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
}
ROOT_URLCONF = "rdwatch.server.urls"
USE_I18N = False
USE_TZ = False
WSGI_APPLICATION = "rdwatch.server.application"
