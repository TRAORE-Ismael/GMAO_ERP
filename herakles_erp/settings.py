"""
Django settings for herakles_erp project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv  # <-- AJOUT
from django.utils.translation import gettext_lazy as _

# Charge les variables d'environnement depuis le fichier .env
load_dotenv()  # <-- AJOUT

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# CONFIGURATION DE SÉCURITÉ ET DE DÉPLOIEMENT
# (Chargée depuis le fichier .env)
# =============================================================================

# La clé secrète est maintenant lue depuis l'environnement
SECRET_KEY = os.getenv('SECRET_KEY')

# Le mode DEBUG est maintenant lu depuis l'environnement
# La conversion en booléen est importante
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Les hôtes autorisés sont lus depuis l'environnement, séparés par des virgules
ALLOWED_HOSTS_str = os.getenv('ALLOWED_HOSTS', '')
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_str.split(',') if host.strip()]
ALLOWED_HOSTS.append('.ngrok-free.app') # On garde ngrok si vous en avez besoin

CSRF_TRUSTED_ORIGINS = ['https://*.ngrok-free.app']


# =============================================================================
# CONFIGURATION DE L'APPLICATION
# =============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_filters',
    'suivi_production',  
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'herakles_erp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'herakles_erp.wsgi.application'

# =============================================================================
# BASE DE DONNÉES
# =============================================================================

# Votre logique existante pour Docker est conservée, elle est très bien.
# Elle utilise déjà les variables d'environnement.
if 'POSTGRES_DB' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB'),
            'USER': os.environ.get('POSTGRES_USER'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
            'HOST': os.environ.get('POSTGRES_HOST'),
            'PORT': '5432',
        }
    }
else:
    # Si on n'est pas dans Docker, on utilise SQLite pour le développement local simple
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# =============================================================================
# VALIDATION DE MOT DE PASSE ET INTERNATIONALISATION
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Internationalisation ---
LANGUAGE_CODE = 'fr' # On peut mettre le français par défaut
LANGUAGES = [
    ('fr', _('Français')),
    ('en', _('English')),
]
LOCALE_PATHS = [ os.path.join(BASE_DIR, 'locale') ]
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# =============================================================================
# FICHIERS STATIQUES ET MÉDIAS
# =============================================================================

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'

# =============================================================================
# CONFIGURATION DIVERS
# =============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = '/dashboard/redirect/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/connexion/'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True