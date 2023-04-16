#!/usr/bin/env bash

export $(grep -v '^#' .env.test | xargs)

pytest --log-cli-level INFO