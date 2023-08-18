#!/usr/bin/env bash

export $(grep -v '^#' .env.test | xargs)

# Start redis server and run it in the background
echo "Starting redis server in the background..."
redis-server --daemonize yes
redis-cli ping

echo "Clearing all redis data..."
redis-cli FLUSHDB

echo "Running tests $1"
pytest --log-cli-level=WARNING -vv $1

# Use this later
# celery -A app.worker worker -Q scheduler-queue -l info
# celery -A app.worker beat