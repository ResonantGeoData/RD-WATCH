from django_redis.client import DefaultClient
from redis import RedisCluster


class CustomRedisCluster(DefaultClient):
    def connect(self, index):
        """Override the connection retrival function."""
        return RedisCluster.from_url(self._server[index])
