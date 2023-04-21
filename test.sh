#!/usr/bin/env bash

export $(grep -v '^#' .env.test | xargs)

echo "Running tests $1"
pytest --log-cli-level WARNING -vv $1