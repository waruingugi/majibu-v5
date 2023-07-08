#!/usr/bin/env bash

export $(grep -v '^#' .env.test | xargs)

echo "Generating coverage report"
pytest --cov --cov-report=html:coverage_re