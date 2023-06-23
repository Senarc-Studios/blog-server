#!/bin/bash
export PYTHONHASHSEED=$(cat config.json | jq -r '.hash_seed')
python3 -m uvicorn main:app --reload --host 127.0.0.1 --workers 2 --port 8000