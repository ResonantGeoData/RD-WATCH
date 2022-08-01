FROM ubuntu:22.04
COPY docker-entrypoint.sh /docker-entrypoint.sh
COPY unit-reloader /usr/local/bin/unit-reloader
RUN apt-get update \
 && apt-get install --no-install-recommends --yes \
      curl \
      entr \
      ripgrep \
 && rm -rf /var/lib/apt/lists/* \
 && chmod +x /docker-entrypoint.sh \
 && chmod +x /usr/local/bin/unit-reloader

ENTRYPOINT [ "/docker-entrypoint.sh" ]
CMD [ "unit-reloader" ]
