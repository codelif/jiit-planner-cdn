#!/usr/bin/bash

./.venv/bin/python3 ./generate_cache.py

git add .
git commit -m "update cache"
