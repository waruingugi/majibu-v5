FROM python:3.10-slim

RUN apt-get update && apt-get install -y postgresql-client

RUN pip install poetry==1.4.2

ENV PYTHONDONTWRITEBYTECODE 1 \
    ENV PYTHONUNBUFFERED 1 \
    ENV POETRY_NO_INTERACTION 1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN poetry config virtualenvs.create false

WORKDIR /majibu

ENV PYTHONPATH=/majibu

COPY pyproject.toml poetry.lock* /majibu/

RUN poetry install --no-root --without dev && rm -rf $POETRY_CACHE_DIR

COPY . /majibu
