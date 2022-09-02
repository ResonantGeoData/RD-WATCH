# Base runtime environment for rdwatch
FROM ubuntu:22.04 AS base
COPY docker/nginx.json /usr/local/etc/unit/config.json
COPY docker/docker-entrypoint.sh /docker-entrypoint.sh
COPY docker/keyrings/nginx.gpg /usr/share/keyrings/nginx.gpg
RUN echo "deb [signed-by=/usr/share/keyrings/nginx.gpg] http://packages.nginx.org/unit/ubuntu/ jammy unit" > /etc/apt/sources.list.d/unit.list \
 && echo "deb-src [signed-by=/usr/share/keyrings/nginx.gpg] http://packages.nginx.org/unit/ubuntu/ jammy unit" >> /etc/apt/sources.list.d/unit.list \
 && apt-get update \
 && apt-get install --no-install-recommends --yes \
      curl \
      libproj22 \
      libgdal30 \
      netcat \
      tzdata \
      unit \
      unit-python3.10 \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir /run/unit \
 && chmod +x /docker-entrypoint.sh \
 && useradd --no-create-home rdwatch \
 && usermod --lock rdwatch \
 && usermod --append --groups rdwatch unit
WORKDIR /app
EXPOSE 80
ENTRYPOINT [ "/docker-entrypoint.sh" ]
CMD [ \
      "unitd", \
        "--no-daemon", \
        "--control", "unix:/run/unit/control.unit.sock", \
        "--user", "unit", \
        "--group", "unit", \
        "--log", "/dev/stdout" \
     ]

# Base builder
FROM base as builder
COPY docker/keyrings/nodesource.gpg /usr/share/keyrings/nodesource.gpg
RUN echo "deb [signed-by=/usr/share/keyrings/nodesource.gpg] http://deb.nodesource.com/node_16.x jammy main" > /etc/apt/sources.list.d/nodesource.list \
 && echo "deb-src [signed-by=/usr/share/keyrings/nodesource.gpg] http://deb.nodesource.com/node_16.x jammy main" >> /etc/apt/sources.list.d/nodesource.list \
 && apt-get update \
 && apt-get install --no-install-recommends --yes \
      build-essential \
      git \
      libgdal-dev \
      libpq-dev \
      nodejs \
      python3-cachecontrol \
      python3-dev \
      python3-poetry \
 && rm -rf /var/lib/apt/lists/* \
 && poetry config installer.parallel true \
 && poetry config virtualenvs.in-project true

FROM builder as vue-builder
WORKDIR /app/vue
COPY vue/package.json vue/package-lock.json /app/vue/
RUN npm ci

FROM builder AS django-builder
WORKDIR /app/django
COPY django/pyproject.toml django/poetry.lock /app/django/
RUN mkdir /app/django/src \
 && mkdir /app/django/src/rdwatch \
 && touch /app/django/src/rdwatch/__init__.py \
 && touch /app/django/README.md \
 && poetry install --no-dev


# Built static assets for vue-rdwatch
#    static assets are in /app/vue/dist
FROM vue-builder AS vue-dist
COPY vue /app/vue
RUN npm run build
RUN chmod -R u=rX,g=rX,o= /app/vue/dist


# Built virtual environment for django-rdwatch
#    editable source is in /app/django/src/rdwatch
#    virtual environment is in /app/django/.venv
FROM django-builder AS django-dist
COPY django/src/rdwatch /app/django/src/rdwatch
RUN chmod -R u=rX,g=rX,o= .


# Final image
FROM base
COPY --from=django-dist \
     --chown=rdwatch:rdwatch \
     /app/django \
     /app/django
COPY --from=vue-dist \
     --chown=unit:unit \
     /app/vue/dist \
     /app/vue/dist
