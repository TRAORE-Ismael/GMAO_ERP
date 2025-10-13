# Aerotrack ERP - Logiciel de Suivi de Production (GPAO)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.x-green.svg)](https://www.djangoproject.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Aerotrack ERP** est une application web full-stack développée avec Django, simulant un système de **Gestion de la Production Assistée par Ordinateur (GPAO)**. Elle permet le suivi en temps réel des opérations en atelier, la gestion des ordres de fabrication, et fournit des tableaux de bord analytiques pour les managers.

Ce projet a été conçu pour démontrer la mise en œuvre d'une logique métier complexe dans un environnement web moderne, conteneurisé avec Docker, sécurisé et réactif.

---

### Aperçu du Tableau de Bord Manager
![Aperçu du Tableau de Bord](https://i.imgur.com/YOUR_IMAGE_ID.png)
*(Pensez à remplacer ce lien par une vraie capture d'écran de votre tableau de bord)*

---

## 📋 Table des Matières
1.  [Fonctionnalités Clés](#-fonctionnalités-clés)
2.  [Technologies Utilisées](#-technologies-utilisées)
3.  [Installation et Lancement (avec Docker)](#-installation-et-lancement-avec-docker)
4.  [Premiers Pas](#-premiers-pas)
5.  [Améliorations Futures](#-améliorations-futures)
6.  [Licence](#-licence)

---

## ✨ Fonctionnalités Clés

-   **Gestion des Rôles** : `Manager` (accès complet) et `Poste` (accès à la saisie).
-   **Gestion des Ordres de Fabrication (OFs)** : Interface CRUD pour définir les OFs et leurs gammes.
-   **Interface de Saisie pour l'Atelier** : Déclaration de début/fin de tâches, quantités et rebuts via une interface **réactive (AJAX)** sans rechargement.
-   **Génération de Codes-Barres** : Pour chaque opération, facilitant la saisie.
-   **Tableau de Bord Manager** : KPIs, graphique de production, et alertes (anomalies, stocks, retards) avec **rafraîchissement automatique** toutes les 30 secondes.
-   **Historique & Archivage** : Consultation des tendances de production sur le long terme et archivage des anciens OFs via des **tâches automatisées**.
-   **Gestion Multilingue** : Interface disponible en Français et en Anglais.

---

## 🛠️ Technologies Utilisées

-   **Backend** : Python 3.10+, Django 5.x, Gunicorn, PostgreSQL.
-   **Frontend** : HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, AJAX (Fetch API), Chart.js.
-   **Conteneurisation** : Docker & Docker Compose.
-   **Reverse Proxy** : Nginx.
-   **Bibliothèques Notables** : `python-barcode`, `python-dotenv`.

---

## 🚀 Installation et Lancement (avec Docker)

Cette méthode est la seule officiellement supportée. Elle garantit que l'application s'exécute dans un environnement contrôlé et identique à la production.

**Prérequis** : Git, Docker et Docker Compose installés sur votre machine.

**1. Cloner le projet**
```bash
git clone https://github.com/TRAORE_Ismael/GMAO_ERP.git
cd GMAO_ERP
```

**2. Configurer l'environnement**
Le projet utilise un fichier `.env` pour les variables de configuration. Copiez le fichier d'exemple fourni :

```bash
# Sur Windows (PowerShell)
copy env.example .env

# Sur macOS/Linux
cp env.example .env
```
Le fichier `.env` par défaut est déjà configuré pour le développement. Vous n'avez rien à modifier pour un premier lancement.

**3. Lancer l'application**
Cette commande va construire les images Docker, démarrer tous les services (web, base de données, nginx, cron) et lancer l'application.

```bash
docker compose up --build -d
```
*(Le `-d` lance les conteneurs en arrière-plan. La première construction peut prendre quelques minutes).

**4. Initialiser la base de données**
Ouvrez un nouveau terminal et exécutez la commande suivante pour créer les tables de la base de données.

```bash
docker compose exec web python manage.py migrate
```

**5. Créer un compte Administrateur**
Cet utilisateur aura un accès complet, y compris à l'interface d'administration de Django.

```bash
docker compose exec web python manage.py createsuperuser
```
Suivez les instructions pour définir un nom d'utilisateur, un e-mail et un mot de passe.

**L'application est prête !**
-   **Site web** : [http://localhost/](http://localhost/) (ou http://localhost:80/)
-   **Admin Django** : [http://localhost/admin/](http://localhost/admin/)

---

## 🧑‍💻 Premiers Pas

1.  **Créer un compte Manager** :
    -   Connectez-vous à l'Admin Django (`/admin/`) avec le super-utilisateur que vous venez de créer.
    -   Allez dans la section "Users", créez un nouvel utilisateur.
    -   Allez dans la section "Profiles", créez un profil pour cet utilisateur et assignez-lui le rôle `MANAGER`.

2.  **Créer un compte Opérateur ("Poste")** :
    -   De la même manière, créez un autre utilisateur et assignez-lui le rôle `POSTE`.

3.  **Se connecter et explorer** :
    -   Déconnectez-vous de l'admin et connectez-vous sur le site principal avec votre compte Manager pour accéder au tableau de bord.
    -   Connectez-vous avec votre compte Poste pour accéder à l'interface de saisie.

---

## 🔮 Améliorations Futures

-   [ ] **Gestion des droits plus fine** via les groupes et permissions de Django.
-   [ ] **Augmenter la couverture de tests unitaires**.
-   [ ] **Notifications en temps réel** avec WebSockets (Django Channels).
-   [ ] **Mise en place d'un pipeline CI/CD** avec GitHub Actions.

---

## 📄 Licence
Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.