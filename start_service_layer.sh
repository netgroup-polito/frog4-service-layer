#!/bin/bash
echo "" > FrogServiceLayer.log
python3 gunicorn.py "$@"
