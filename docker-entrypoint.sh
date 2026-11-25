#!/bin/sh
set -e
# Datenbank-Migrationen bei jedem Start einspielen (idempotent)
python manage.py migrate --noinput
exec "$@"
