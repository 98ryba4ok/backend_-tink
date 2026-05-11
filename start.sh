#!/bin/sh
python manage.py makemigrations movies users events recommendations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser --no-input || true
uvicorn cinefind.asgi:application --host 0.0.0.0 --port $PORT
