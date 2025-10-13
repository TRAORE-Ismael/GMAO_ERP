# Herakles ERP - Logiciel de Suivi de Production (GPAO)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.x-green.svg)](https://www.djangoproject.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Herakles ERP** est une application web full-stack développée avec Django, simulant un système de **Gestion de la Production Assistée par Ordinateur (GPAO)**. Elle permet le suivi en temps réel des opérations en atelier, la gestion des ordres de fabrication, des stocks, et fournit des tableaux de bord analytiques pour les managers.

Ce projet a été conçu pour démontrer la mise en œuvre d'une logique métier complexe dans un environnement web moderne, sécurisé et réactif, en utilisant les meilleures pratiques de développement Django et une architecture orientée services via des appels AJAX.

---

### Tableau de Bord Manager
![Aperçu du Tableau de Bord](https://i.imgur.com/YOUR_IMAGE_ID.png)
*(Pensez à remplacer ce lien par une vraie capture d'écran de votre tableau de bord)*

---

## 📋 Table des Matières
1.  [Fonctionnalités Clés](#-fonctionnalités-clés)
2.  [Architecture Technique](#-architecture-technique)
3.  [Technologies Utilisées](#-technologies-utilisées)
4.  [Installation et Lancement](#-installation-et-lancement)
5.  [Utilisation](#-utilisation)
6.  [Améliorations Futures](#-améliorations-futures)

---

## ✨ Fonctionnalités Clés

### 1. Gestion des Utilisateurs et des Rôles
-   **Système d'Authentification Complet** : Inscription, connexion et déconnexion sécurisées.
-   **Gestion des Rôles** :
    -   **Manager** : Accès complet au suivi, aux tableaux de bord, à la gestion des OFs, des matières et des machines.
    -   **Poste de Travail** : Accès restreint à l'interface de saisie des temps pour les opérations.
-   **Redirection Automatique** : Les utilisateurs sont redirigés vers leur interface respective après connexion.

### 2. Module de Production (GPAO)
-   **Gestion des Ordres de Fabrication (OFs)** : Interface CRUD complète pour définir les OFs et leurs gammes d'opérations.
-   **Interface de Saisie pour l'Atelier** :
    -   Déclaration du début et de la fin des opérations via un système de "scan" (simulation par clic).
    -   Déclaration des quantités fabriquées et des rebuts.
    -   Interface **réactive (AJAX)** pour une expérience utilisateur fluide sans rechargement de page.
-   **Génération de Fiches de Fabrication** : Fiches imprimables incluant les **codes-barres** pour chaque opération.

### 3. Gestion des Ressources
-   **Gestion des Stocks** : Catalogue des matières premières, association aux opérations (nomenclature) et **décrémentation automatique des stocks** en temps réel.
-   **Gestion du Parc Machines** : Catalogue des machines avec suivi de leur statut (Disponible, En panne, Maintenance).

### 4. Reporting et Suivi
-   **Tableau de Bord Manager** : Vue synthétique avec KPIs en temps réel (opérations en cours, opérateurs actifs, production, taux de rebut) et **graphique** de l'historique de production.
-   **Suivi Détaillé** : Vue tabulaire de tous les pointages avec des options de **filtrage** avancées.
-   **Export de Données** : Export de la vue de suivi au format **CSV**.

---

## 🏗️ Architecture Technique

L'application est construite autour d'une architecture Django standard, avec une séparation claire entre le backend et le frontend.

-   **Backend (Django)** : Gère toute la logique métier, l'accès à la base de données via l'ORM, l'authentification et expose des endpoints API pour le frontend.
-   **Frontend (JavaScript/AJAX)** : L'interface de saisie en atelier est une **Single Page Application (SPA)** de-facto. Elle communique avec le backend via des appels `fetch` (AJAX) pour :
    -   Récupérer les informations d'un OF.
    -   Démarrer et arrêter un pointage.
    -   Valider une production (quantités et rebuts).
    -   Signaler une anomalie.
    
Cette approche permet une interactivité maximale sans recharger la page, simulant une application de bureau moderne.

---

## 🛠️ Technologies Utilisées

-   **Backend** :
    -   **Python 3.10+**
    -   **Django 5.x**
    -   **Gunicorn** & **Waitress** : Serveurs d'application WSGI.
    -   **Base de données** : PostgreSQL (en production via Docker), SQLite3 (en développement local).
-   **Frontend** :
    -   **HTML5, CSS3, JavaScript (ES6+)**
    -   **Bootstrap 5** : Framework CSS pour un design responsive.
    -   **AJAX (Fetch API)** : Pour la communication asynchrone.
    -   **Chart.js** : Pour les graphiques interactifs.
-   **Conteneurisation** :
    -   **Docker** & **Docker Compose** : Pour une mise en production et un développement standardisés.
    -   **Nginx** : Comme reverse proxy pour servir les fichiers statiques et l'application Django.
-   **Bibliothèques Python Notables** :
    -   `python-barcode` : Pour la génération des codes-barres SVG.

---

## 🚀 Installation et Lancement

### Option 1 : Avec Docker (Recommandé)

Cette méthode est la plus simple pour lancer l'application avec une configuration similaire à la production.

**Prérequis** : Docker et Docker Compose installés.

1.  **Cloner le projet** :
    ```bash
    git clone https://votre-lien-vers-le-repo.git
    cd GMAO_ERP
    ```

2.  **Lancer les conteneurs** :
    ```bash
    docker-compose up --build
    ```
    
    L'application sera accessible à l'adresse [http://localhost:8000](http://localhost:8000).

### Option 2 : Installation Manuelle Locale

1.  **Cloner le projet** et naviguer dans le dossier.

2.  **Créer un environnement virtuel** :
    ```bash
    python -m venv tdm
    ```

3.  **Activer l'environnement** :
    -   Sur Windows : `tdm\Scripts\activate`
    -   Sur macOS/Linux : `source tdm/bin/activate`

4.  **Installer les dépendances** :
    ```bash
    pip install -r requirements.txt
    ```

5.  **Appliquer les migrations** :
    ```bash
    python manage.py migrate
    ```

6.  **Lancer le serveur de développement** :
    ```bash
    python manage.py runserver
    ```
    L'application sera accessible à l'adresse [http://localhost:8000](http://localhost:8000).

---

## 🧑‍💻 Utilisation

1.  **Créer des comptes** :
    -   Rendez-vous sur la page d'accueil et utilisez le formulaire d'inscription.
    -   Le premier utilisateur créé sera un simple "Poste". Pour créer un "Manager", vous devrez modifier son rôle directement dans la base de données ou via l'interface d'administration de Django (après avoir créé un superutilisateur avec `python manage.py createsuperuser`).

2.  **Se connecter** :
    -   Un utilisateur avec le rôle **Manager** sera redirigé vers le tableau de bord.
    -   Un utilisateur avec le rôle **Poste** sera redirigé vers l'interface de saisie.

---

## 🔮 Améliorations Futures
-   [ ] **Gestion des Droits plus Fine** : Utiliser les groupes et permissions de Django.
-   [ ] **Tests Unitaires** : Augmenter la couverture de tests pour la logique métier.
-   [ ] **Notifications en Temps Réel** : Utiliser WebSockets pour les alertes (anomalies, stocks bas).
-   [ ] **Intégration CI/CD** : Mettre en place un pipeline avec GitHub Actions pour automatiser les tests et le déploiement.

---

## 📄 License
Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

### 3. Configurer la Base de Données
Le projet est configuré pour utiliser SQLite par défaut, aucune configuration supplémentaire n'est requise.
```bash
# Créer les fichiers de migration
python manage.py makemigrations

# Appliquer les migrations pour créer la base de données
python manage.py migrate
```

### 4. Créer un Super-Utilisateur
Cet utilisateur aura accès à l'interface d'administration de Django.
```bash
python manage.py createsuperuser
```
Suivez les instructions pour créer votre compte administrateur.

### 5. Lancer le Serveur de Développement
```bash
python manage.py runserver
```

L'application est maintenant accessible à l'adresse **http://127.0.0.1:8000/**.

---

### Utilisation
1.  Accédez à l'application.
2.  Créez un compte **Manager** via le formulaire d'inscription.
3.  Connectez-vous avec ce compte.
4.  Utilisez l'interface d'administration (`/admin/`) ou la section "Gestion des OFs" pour créer des `MatierePremiere`, des `Machine`, des `Operateur`, et un `OrdreFabrication` avec ses opérations.
5.  Déconnectez-vous et créez un compte **Poste de Travail**.
6.  Connectez-vous avec ce second compte pour accéder à l'interface de saisie et simuler la production.