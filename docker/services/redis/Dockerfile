FROM redis:7
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT [ "/docker-entrypoint.sh" ]
CMD [ \
      "redis-server", \
        "--aclfile", "/etc/redis.acl", \
        "--save", "60", "1", \
        "--loglevel", "warning" \
     ]
