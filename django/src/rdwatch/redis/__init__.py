from redis import RedisCluster
from django_redis.client import DefaultClient


class CustomRedisCluster(DefaultClient):
    def connect(self, index):
        """Override the connection retrival function."""
        return RedisCluster.from_url(self._server[index])
