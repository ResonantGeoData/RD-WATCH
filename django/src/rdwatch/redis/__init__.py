from django_redis.client import DefaultClient
from redis import RedisCluster


# Unfortunately, django-redis does not support Redis cluster mode.
# See relevant issue here https://github.com/jazzband/django-redis/issues/606.
#
# The class below is based on the workaround found here:
# https://github.com/jazzband/django-redis/issues/208
# Once either django-redis or the native Django redis driver supports
# cluster mode, this should be removed in favor of that.
class CustomRedisCluster(DefaultClient):
    def connect(self, index):
        """Override the connection retrival function."""
        return RedisCluster.from_url(self._server[index])
