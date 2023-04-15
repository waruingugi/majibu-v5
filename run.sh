#!/usr/bin/env bash

# Uncomment command below if you are having 
# ´ModuleNotFoundError: No module named 'app´ errors 
export PYTHONPATH=$PWD

# Start redis server and run it in the background
redis-server --daemonize yes

# Check if background redis-server started successfully
# ps aux | grep redis-server

# To stop redis server running in background
# sudo /etc/init.d/redis-server stop

python app/backend_pre_start.py
uvicorn usgi:app --reload --host 127.0.0.1