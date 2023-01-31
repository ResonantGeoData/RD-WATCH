from redis import RedisCluster


class CustomRedisClient(RedisCluster):
    def __init__(self, url, **kwargs):
        client = RedisCluster.from_url(url)
        kwargs["startup_nodes"] = client.get_nodes()
        del kwargs["connection_pool"]
        super().__init__(**kwargs)
