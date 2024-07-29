import os
from datetime import timedelta
from pathlib import Path

from configurations import Configuration, values

_ENVIRON_PREFIX = 'RDWATCH'


# With the default "late_binding=False", and "environ_name" is
# specified or "environ=False", even Values from non-included
# classes (e.g. `AWS_DEFAULT_REGION) get immediately evaluated and
# expect env vars to be set.
values.Value.late_binding = True


class BaseConfiguration(Configuration):
    ROOT_URLCONF = 'rdwatch.urls'
    USE_I18N = False
    USE_TZ = False
    USE_X_FORWARDED_HOST = True
    WSGI_APPLICATION = 'rdwatch.wsgi.application'
    ALLOWED_HOSTS = ['*']
    DEBUG = values.BooleanValue(False, environ_prefix='RDWATCH_DJANGO')
    # Django's docs suggest that STATIC_URL should be a relative path,
    # for convenience serving a site on a subpath.
    STATIC_URL = 'static/'

    BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

    @property
    def STATIC_ROOT(self) -> str:
        path = Path(self.BASE_DIR) / 'staticfiles'
        if path.exists() and not path.is_dir():
            raise ValueError(f'Path {repr(path)} is not a directory.')
        path.mkdir(exist_ok=True)
        return str(path)

    # The `/accounts/*` endpoints are the only endpoints that should *not*
    # require authentication to access
    LOGIN_REQUIRED_IGNORE_PATHS = [
        r'/accounts/',  # allow unauthenticated access to the accounts endpoints
        r'/api/',  # ninja will handle authentication for the REST API
    ]

    SAM_CHECKPOINT_MODEL = values.PathValue(
        '/data/SAM/sam_vit_h_4b8939.pth',
        environ_prefix='RDWATCH_DJANGO',
        check_exists=False,
    )

    @property
    def INSTALLED_APPS(self):
        base_applications = [
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            # Must go before django.contrib.staticfiles
            # https://whitenoise.readthedocs.io/en/stable/django.html#using-whitenoise-in-development
            'whitenoise.runserver_nostatic',
            'django.contrib.staticfiles',
            'django.contrib.gis',
            'django.contrib.postgres',
            'django_extensions',
            'django_celery_results',
            'allauth',
            'allauth.account',
            'allauth.socialaccount',
            'allauth.socialaccount.providers.gitlab',
            'django_rename_app',  # TODO: remove this when migration is complete
            'rdwatch.core.apps.RDWatchConfig',
        ]
        if 'RDWATCH_POSTGRESQL_SCORING_URI' in os.environ:
            base_applications.append('rdwatch.scoring.apps.ScoringConfig')
        if all(
            os.environ.get(key)
            for key in [
                'RDWATCH_SMARTFLOW_URL',
                'RDWATCH_SMARTFLOW_USERNAME',
                'RDWATCH_SMARTFLOW_PASSWORD',
            ]
        ):
            base_applications.append('rdwatch.smartflow.apps.SmartflowConfig')
        return base_applications

    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        # Must be placed "above all other middleware apart
        # from Django’s SecurityMiddleware"
        # https://whitenoise.readthedocs.io/en/stable/index.html#quickstart-for-django-apps
        'whitenoise.middleware.WhiteNoiseMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'login_required.middleware.LoginRequiredMiddleware',
        'allauth.account.middleware.AccountMiddleware',
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

    AUTHENTICATION_BACKENDS = [
        # Needed for django-allauth
        'django.contrib.auth.backends.ModelBackend',
        'allauth.account.auth_backends.AuthenticationBackend',
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

    NINJA_PAGINATION_CLASS = 'ninja.pagination.PageNumberPagination'
    NINJA_PAGINATION_PER_PAGE = 100

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

    SMARTFLOW_URL = values.Value(
        None,
        environ_required=False,
        environ_prefix=_ENVIRON_PREFIX,
    )

    SMARTFLOW_USERNAME = values.Value(
        None,
        environ_required=False,
        environ_prefix=_ENVIRON_PREFIX,
    )
    SMARTFLOW_PASSWORD = values.Value(
        None,
        environ_required=False,
        environ_prefix=_ENVIRON_PREFIX,
    )
    MODEL_RUN_API_KEY = values.SecretValue(
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
            return ['rdwatch.scoring.router.ScoringRouter']
        else:
            return []

    CELERY_BEAT_SCHEDULE = {
        'collect-garbage-beat': {
            'task': 'rdwatch.core.tasks.collect_garbage_task',
            'schedule': timedelta(hours=1),
        },
    }


class DevelopmentConfiguration(BaseConfiguration):
    SECRET_KEY = 'secretkey'  # Dummy value for local development configuration

    STORAGES = {
        'default': {
            'BACKEND': 'minio_storage.storage.MinioMediaStorage',
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }

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

    # Install django-debug-toolbar in development
    @property
    def INSTALLED_APPS(self) -> list[str]:
        return super().INSTALLED_APPS + ['debug_toolbar']

    @property
    def MIDDLEWARE(self) -> list[str]:
        return super().MIDDLEWARE + ['debug_toolbar.middleware.DebugToolbarMiddleware']

    # This is needed for django-debug-toolbar
    @property
    def INTERNAL_IPS(self) -> list[str]:
        return super().INTERNAL_IPS + ['127.0.0.1']


# Based on
# https://github.com/kitware-resonant/django-composed-configuration/blob/master/composed_configuration/_configuration.py#L65
class TestingConfiguration(BaseConfiguration):
    SECRET_KEY = 'testingsecret'

    # Testing will add 'testserver' to ALLOWED_HOSTS
    ALLOWED_HOSTS: list[str] = []

    MINIO_STORAGE_MEDIA_BUCKET_NAME = 'test-django-storage'

    # Testing will set EMAIL_BACKEND to use the memory backend


class ProductionConfiguration(BaseConfiguration):
    SECRET_KEY = values.Value(environ_required=True, environ_prefix=_ENVIRON_PREFIX)

    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }

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

    # Django runs behind an nginx in production. nginx strips the HTTPS protocol
    # from the request before proxing it to Django, so we need to tell Django to
    # assume the presence of the X-Forwarded-Proto header indicates HTTPS.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # Override the default allauth adapters so we can implement a custom authorization
    # flow based on the user's GitLab group membership
    ACCOUNT_ADAPTER = 'rdwatch.allauth.RDWatchAccountAdapter'
    SOCIALACCOUNT_ADAPTER = 'rdwatch.allauth.RDWatchSocialAccountAdapter'

    # Configure django-allauth to store access tokens for in the database instead of
    # discarding them after use. This allows us to retrieve it later in the
    # RDWatchSocialAccountAdapter to use for checking the user's
    # GitLab group membership.
    SOCIALACCOUNT_STORE_TOKENS = True

    SOCIALACCOUNT_PROVIDERS = {
        'gitlab': {
            'SCOPE': ['read_user', 'openid'],
            'APPS': [
                {
                    'client_id': os.environ.get('RDWATCH_GITLAB_OAUTH_APP_ID'),
                    'secret': os.environ.get('RDWATCH_GITLAB_OAUTH_SECRET'),
                    'settings': {
                        'gitlab_url': os.environ.get('RDWATCH_GITLAB_OAUTH_URL'),
                    },
                }
            ],
        },
    }

    # The GitLab groups that are allowed to access the site
    ALLOWED_GITLAB_GROUPS = values.ListValue(
        environ_prefix=_ENVIRON_PREFIX,
        environ_name='ALLOWED_GITLAB_GROUPS',
        environ_required=True,
    )

    # All login attempts in production should go straight to GitLab
    LOGIN_URL = '/accounts/gitlab/login/'

    ACCOUNT_EMAIL_VERIFICATION = 'none'
