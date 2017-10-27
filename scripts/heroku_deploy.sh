#!/usr/bin/env bash

echo "Collecting Static Files..."
python manage.py collectstatic --noinput

echo "Running Migration..."
python manage.py migrate