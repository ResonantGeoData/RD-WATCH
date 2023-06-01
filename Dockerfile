# Base runtime environment for rdwatch
FROM ubuntu:22.10 AS base
COPY docker/nginx.json /usr/local/etc/unit/config.json
COPY docker/docker-entrypoint.sh /docker-entrypoint.sh
COPY docker/keyrings/nginx.gpg /usr/share/keyrings/nginx.gpg
RUN echo "deb [signed-by=/usr/share/keyrings/nginx.gpg] http://packages.nginx.org/unit/ubuntu/ jammy unit" > /etc/apt/sources.list.d/unit.list \
 && echo "deb-src [signed-by=/usr/share/keyrings/nginx.gpg] http://packages.nginx.org/unit/ubuntu/ jammy unit" >> /etc/apt/sources.list.d/unit.list \
 && apt-get update \
 && apt-get install --no-install-recommends --yes \
      ca-certificates \
      curl \
      libproj25 \
      libgdal31 \
      netcat-openbsd \
      python3-cachecontrol \
      python3-pip \
      tzdata \
      unit \
      unit-python3.10 \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir /run/unit \
 && chmod +x /docker-entrypoint.sh \
 && useradd --no-create-home rdwatch \
 && usermod --lock rdwatch \
 && usermod --append --groups rdwatch unit
RUN python3 -m pip install poetry==1.4.2
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
RUN mkdir -p /poetry/venvs
RUN apt-get update \
 && apt-get install --no-install-recommends --yes \
      build-essential \
      git \
      libgdal-dev \
      libpq-dev \
      nodejs \
      npm \
      python3-dev \
 && rm -rf /var/lib/apt/lists/* \
 && poetry config installer.parallel true \
 && poetry config virtualenvs.in-project false \
 && poetry config virtualenvs.path /poetry/venvs

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
 && poetry install --only main


# Build stage that also installs dev dependencies.
# For use in a development environment.
FROM builder AS dev
WORKDIR /app/django
COPY django/pyproject.toml django/poetry.lock /app/django/
RUN mkdir /app/django/src \
 && mkdir /app/django/src/rdwatch \
 && touch /app/django/src/rdwatch/__init__.py \
 && touch /app/django/README.md \
 && poetry install --with dev


# Built static assets for vue-rdwatch
#    static assets are in /app/vue/dist
FROM vue-builder AS vue-dist
COPY vue /app/vue
# include gitHash and date in the client for debugging purposes
COPY .git/ /app/
RUN npm run build
RUN chmod -R u=rX,g=rX,o= /app/vue/dist


# Built virtual environment for django-rdwatch
#    editable source is in /app/django/src/rdwatch
#    virtual environment is in /app/django/.venv
FROM django-builder AS django-dist
COPY django/src/rdwatch /app/django/src/rdwatch
COPY django/src/manage.py /app/django/src/manage.py
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
