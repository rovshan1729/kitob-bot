import os
import hashlib
from pathlib import Path
from environs import Env
from django.utils.translation import gettext_lazy as _

env = Env()
if not os.path.exists('.env'):
    print('.env fayli topilmadi!')
    print('.env.example faylidan nusxa ko\'chirib shablonni o\'zizga moslang.')
    exit(1)

env.read_env()

API_TOKEN = env.str('API_TOKEN')
SECRET_KEY = env.str('SECRET_KEY')
WEB_DOMAIN = env.str('WEB_DOMAIN')
DEBUG = env.bool('DEBUG')
ADMINS = env.list('ADMINS')
CHANNELS = env.list('CHANNELS')

WEBHOOK_PATH = 'tgbot/' + hashlib.md5(API_TOKEN.encode()).hexdigest()
WEBHOOK_URL = f"{WEB_DOMAIN}/{WEBHOOK_PATH}"

LANGUAGES = (
    ("uz", "O'zbekcha"),
    ("ru", "Русский"),
)

BASE_DIR = Path(__file__).resolve().parent.parent

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tgbot',

    ###
    "rest_framework",
    "drf_yasg",
    "corsheaders",
    "modeltranslation",
    "captcha",
    "ckeditor",
    'rosetta',
    "celery",
    "django_celery_beat",
    "import_export",
    "solo.apps.SoloAppConfig",
    'auditlog',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'src.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'src.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    # Postgresql
    "default": {
        "ENGINE": env.str("DB_ENGINE"),
        "NAME": env.str("DB_NAME"),
        "USER": env.str("DB_USER"),
        "PASSWORD": env.str("DB_PASS"),
        "HOST": env.str("DB_HOST"),
        "PORT": env.str("DB_PORT"),
    },
}

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'ru'

TIME_ZONE = "Asia/Tashkent"

USE_I18N = True

USE_TZ = True

CELERY_TIMEZONE = 'Asia/Tashkent'

CELERY_ENABLE_UTC = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
# CSRF_COOKIE_SECURE = False
# CSRF_COOKIE_HTTPONLY = False

# Example Redis credentials
# In production, replace these with secure environment variables or a configuration file
REDIS_HOST = env.str("REDIS_HOST", "redis")
REDIS_PORT = env.int("REDIS_PORT", 6379)
REDIS_DB = env.int("REDIS_DB", 0)
REDIS_URL=f'{REDIS_HOST}://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

I18N_DOMAIN = "django"
LOCALES_DIR = BASE_DIR / "locale"
RECAPTCHA_PUBLIC_KEY = env.str("RECAPTCHA_PUBLIC_KEY", "6LdlOWYpAAAAAOEsejvu7mT-tYr9PBmMlYbVio7R")
RECAPTCHA_PRIVATE_KEY = env.str("RECAPTCHA_PRIVATE_KEY", "6LdlOWYpAAAAAP2nediVlYsjEXrFZpzH4DZlUarQ")

BACK_END_URL = env.str("BACK_END_URL", "https://uic-games-bot.uicgroup.tech")
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False
CSRF_TRUSTED_ORIGINS = [
   "https://uic-games-bot.uicgroup.tech",
   "http://uic-games-bot.uicgroup.tech"
]

# Celery settings
CELERY_BROKER_URL = env.str("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

# CSRF settings
CSRF_TRUSTED_ORIGINS = [
    'https://kitob.uicgroup.tech'
]
