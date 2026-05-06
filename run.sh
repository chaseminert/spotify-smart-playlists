#!/bin/bash
RELATIVE_VENV_PATH=venv/bin/python
cd "$(dirname "$0")"
if [ ! -f "$RELATIVE_VENV_PATH" ]; then
    echo "File not found! Exiting..."
    exit 1
fi
$RELATIVE_VENV_PATH main.py "$@"
