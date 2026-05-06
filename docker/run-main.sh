#!/bin/sh
set -eu

cd /app
mkdir -p /app/.spotipy-cache

exec python main.py "$@"
