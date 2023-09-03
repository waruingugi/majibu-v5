#!/bin/bash

# This file is run by heroku befor launching dynos

# Uncomment command below if you are having 
# ´ModuleNotFoundError: No module named 'app´ errors 
export PYTHONPATH=$PWD

alembic upgrade head

python app/backend_pre_start.py
