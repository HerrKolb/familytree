"""
FamilyTree – Django Settings

Alle betriebsrelevanten Werte kommen aus Umgebungsvariablen (.env).
Produktion: hinter Caddy + Authentik, Login per Header (siehe tree/auth.py).
Lokale Entwicklung: DJANGO_DEBUG=True, AUTH_MODE=local, DB_ENGINE=sqlite.
"""
from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent


def env_list(name, default=''):
    return [v.strip() for v in os.environ.get(name, default).split(',') if v.strip()]


# --- Grundeinstellungen -----------------------------------------------------
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'nur-fuer-lokale-entwicklung'
    else:
        raise RuntimeError('DJANGO_SECRET_KEY muss gesetzt sein.')

ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1')
CSRF_TRUSTED_ORIGINS = env_list('DJANGO_CSRF_TRUSTED_ORIGINS')

# Hinter Caddy: HTTPS erkennen
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# --- Anmeldung --------------------------------------------------------------
# AUTH_MODE=authentik: Benutzer kommt aus den Headern von Authentik (Produktion)
# AUTH_MODE=local:     klassisches Django-Login (nur lokale Entwicklung)
AUTH_MODE = os.environ.get('AUTH_MODE', 'authentik')

# Authentik-Gruppen, die Zugriff auf familytree haben bzw. Admin sind
AUTHENTIK_ALLOWED_GROUPS = env_list('AUTHENTIK_ALLOWED_GROUPS', 'admin,familie')
AUTHENTIK_ADMIN_GROUPS = env_list('AUTHENTIK_ADMIN_GROUPS', 'admin')

# Abmelden über den Authentik-Outpost (beendet die Sitzung für alle Apps)
LOGOUT_URL_EXTERNAL = os.environ.get('LOGOUT_URL_EXTERNAL', '/outpost.goauthentik.io/sign_out')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tree',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if AUTH_MODE == 'authentik':
    # direkt nach AuthenticationMiddleware einfügen
    MIDDLEWARE.insert(
        MIDDLEWARE.index('django.contrib.auth.middleware.AuthenticationMiddleware') + 1,
        'tree.auth.AuthentikHeaderMiddleware',
    )
    AUTHENTICATION_BACKENDS = ['tree.auth.AuthentikBackend']
else:
    AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']

ROOT_URLCONF = 'familytree.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'tree.context_processors.now',
                'tree.context_processors.auth_mode',
            ],
        },
    },
]

WSGI_APPLICATION = 'familytree.wsgi.application'

# --- Datenbank --------------------------------------------------------------
# DB_ENGINE=postgres (Standard, Server), mysql (nur für den einmaligen
# Import der alten Daten) oder sqlite (lokale Entwicklung)
DB_ENGINE = os.environ.get('DB_ENGINE', 'postgres')

if DB_ENGINE == 'postgres':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME':     os.environ.get('DB_NAME', 'familytree'),
            'USER':     os.environ.get('DB_USER', 'familytree'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST':     os.environ.get('DB_HOST', 'db'),
            'PORT':     os.environ.get('DB_PORT', '5432'),
        }
    }
elif DB_ENGINE == 'mysql':
    import pymysql
    pymysql.install_as_MySQLdb()
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME':     os.environ.get('DB_NAME', 'familytree'),
            'USER':     os.environ.get('DB_USER', 'root'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST':     os.environ.get('DB_HOST', 'localhost'),
            'PORT':     os.environ.get('DB_PORT', '3306'),
            'OPTIONS': {'charset': 'utf8mb4'},
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'de-de'
TIME_ZONE = 'Europe/Berlin'
USE_I18N = True
USE_TZ = True

# --- Statische Dateien (über WhiteNoise ausgeliefert) -----------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

# --- Media (Fotos) ----------------------------------------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = Path(os.environ.get('MEDIA_ROOT', BASE_DIR / 'media'))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Login/Logout (nur AUTH_MODE=local) -------------------------------------
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# --- E-Mail (derzeit nicht genutzt; Einladungen laufen über Authentik) ------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.ionos.de')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '465'))
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('EMAIL_FROM', EMAIL_HOST_USER or 'webmaster@localhost')

# --- Logging: Fehler im Container-Log sichtbar machen -----------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
}
