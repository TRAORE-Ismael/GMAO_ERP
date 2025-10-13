#!/bin/sh

# On démarre le service cron en arrière-plan
cron

# On lance le serveur Gunicorn en avant-plan (ce processus gardera le conteneur en vie)
exec gunicorn aerotrack_erp.wsgi:application --bind 0.0.0.0:8000