#!/usr/bin/env bash

export $(grep -v '^#' .env.test | xargs)

pytest