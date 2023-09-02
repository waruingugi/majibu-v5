#!/usr/bin/env bash

# THIS EXECUTABLE IS ONLY USED BY HEROKU
# DO NOT RUN IT LOCALLY!!

# Override these variables with those Heroku has provided
echo "Overriding environment variables set by user..."
export ASYNC_SQLALCHEMY_DATABASE_URI="$DATABASE_URL"
export SQLALCHEMY_DATABASE_URI="$DATABASE_URL"

export CELERY_BROKER="$REDIS_URL"
export CELERY_RESULT_BACKEND="$REDIS_URL"

# Start redis server and run it in the background
echo "Starting redis server in the background..."
redis-server --daemonize yes

echo "Clearing all redis data..."
redis-cli FLUSHDB
