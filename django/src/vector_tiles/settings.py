import os
import dj_database_url

DEBUG = False
SECRET_KEY = os.environ['RDWATCH_SECRET_KEY']
ROOT_URLCONF = 'urls'
ALLOWED_HOSTS = ['*']
INSTALLED_APPS = ['rdwatch']
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'KEY_PREFIX': 'rdwatch',
        'LOCATION': os.environ['RDWATCH_REDIS_URI'],
    }
}
DATABASES = {
    'default': dj_database_url.parse(
        os.environ['RDWATCH_POSTGRESQL_URI'],
        engine='django.contrib.gis.db.backends.postgis',
    )
}

if 'RDWATCH_POSTGRESQL_SCORING_URI' in os.environ:
    DATABASES |= {
        'scoringdb': dj_database_url.parse(
            os.environ['RDWATCH_POSTGRESQL_SCORING_URI'],
            engine='django.contrib.gis.db.backends.postgis',
        )
    }
    INSTALLED_APPS.append('rdwatch_scoring')
