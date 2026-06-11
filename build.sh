#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate

# One-time deployment bootstrap.
# Remove this line after the first successful Render deployment.
python manage.py create_startup_superuser
