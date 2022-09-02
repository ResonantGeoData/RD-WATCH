FROM postgres:14
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates \
      postgresql-14-postgis-3 \
      postgresql-14-postgis-3-scripts \
 && rm -rf /var/lib/apt/lists/*
ENV POSTGRES_USER=rdwatch
COPY ./initdb.sh /docker-entrypoint-initdb.d/10_initdb.sh
