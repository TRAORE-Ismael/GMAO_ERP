# Étape 1: Utiliser une image Python officielle comme base
FROM python:3.10-slim

# Définir des variables d'environnement
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Définir le répertoire de travail à l'intérieur du conteneur
WORKDIR /app

# Copier le fichier des dépendances
COPY requirements.txt /app/

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt


# On met à jour les paquets système et on installe cron
RUN apt-get update && apt-get install -y cron

# On crée le dossier pour les logs
RUN mkdir -p /app/logs && touch /app/logs/cron.log

# On crée notre fichier crontab directement dans l'image
# Note : on utilise echo et tee pour écrire dans le fichier
RUN echo "5 1 * * *    /usr/local/bin/python /app/manage.py generer_rapport_quotidien >> /app/logs/cron.log 2>&1" | tee /etc/cron.d/aerotrack-cron
RUN echo "5 2 * * 1    /usr/local/bin/python /app/manage.py archiver_ofs --jours 1 >> /app/logs/cron.log 2>&1" | tee -a /etc/cron.d/aerotrack-cron

# On donne les bonnes permissions
RUN chmod 0644 /etc/cron.d/aerotrack-cron

# Copier tout le code du projet dans le conteneur
COPY . /app/

RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
# Exposer le port que notre application utilisera
EXPOSE 8000