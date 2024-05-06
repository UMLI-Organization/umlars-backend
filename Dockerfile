FROM python:3.11.5-slim-bookworm AS umli_backend_dev_build

ARG UMLI_IN_ENV

ENV UMLI_IN_ENV=${UMLI_IN_ENV} \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  # Poetry's configuration:
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  POETRY_HOME='/usr/local' \
  POETRY_VERSION=1.7.1

# System deps:
RUN apt-get update \
&& apt-get install --no-install-recommends -y \
    bash \
    build-essential \
    curl \
    gettext \
    git \
    libpq-dev \
    wget \
# Cleaning cache:
&& apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/* \
# Poetry:
&& curl -sSL https://install.python-poetry.org | python - \
&& poetry --version

# Copy only requirements to cache them in docker layer
WORKDIR /code

COPY pyproject.toml poetry.lock Makefile /code/

# Project initialization:
RUN make docker-setup

# TODO: For a production use the below COPY statement instead of the volume in docker-compose.yml build
# Creating folders, and files for a project:
COPY . /code