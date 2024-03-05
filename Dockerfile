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


# FROM python:3.10-slim

# RUN pip install poetry==1.4.2

# ENV PYTHONDONTWRITEBYTECODE 1 \
#     ENV PYTHONUNBUFFERED 1 \
#     ENV POETRY_NO_INTERACTION 1 \
#     POETRY_CACHE_DIR=/tmp/poetry_cache

# RUN poetry config virtualenvs.create false

# WORKDIR /majibu

# ENV PYTHONPATH=/majibu

# COPY pyproject.toml poetry.lock* /majibu/

# RUN poetry install --no-root --without dev && rm -rf $POETRY_CACHE_DIR

# COPY . /majibu

# RUN chmod +x run.sh

# CMD ["uvicorn", "usgi:app", "--reload", "--host", "0.0.0.0", "--port", "9000"]


# FROM python:3.10-slim as base

# RUN pip install poetry==1.4.2

# ENV PYTHONDONTWRITEBYTECODE 1
# ENV PYTHONUNBUFFERED 1
# ENV POETRY_NO_INTERACTION=1 \
#     POETRY_VIRTUALENVS_IN_PROJECT=1 \
#     POETRY_VIRTUALENVS_CREATE=1 \
#     POETRY_CACHE_DIR=/tmp/poetry_cache

# WORKDIR /majibu

# COPY pyproject.toml poetry.lock* /majibu/

# RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

# FROM python:3.10-slim as builder

# ENV VIRTUAL_ENV=/majibu/.venv \
#     PATH="/majibu/.venv/bin:$PATH"

# COPY --from=base ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# COPY . /majibu

# WORKDIR /majibu

# RUN chmod +x run.sh

# ENTRYPOINT ["./run.sh"]
