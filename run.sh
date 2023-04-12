#!/usr/bin/env bash

# Uncomment command below if you are having 
# ´ModuleNotFoundError: No module named 'app´ errors 
export PYTHONPATH=$PWD

python app/backend_pre_start.py
uvicorn usgi:app --reload --host 127.0.0.1