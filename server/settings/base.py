"""
Django settings for server project.

Generated by 'django-admin startproject' using Django 3.0.8.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

from corsheaders.defaults import default_headers
import os


def get_secret(secret_id, backup=None):
    return os.getenv(secret_id, backup)


# Security
DEBUG = True
SECRET_KEY = get_secret('SECRET_KEY', '28m)4%dfc#1aez26*enbl5n(#($%c6ge_&l6*lvvhx9weybqv#')

# File System
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Application definition
INSTALLED_APPS = [
    # CORS
    'corsheaders',
    # Default
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Coded Apps
    'accounts.apps.AccountsConfig',
    'projects.apps.ProjectsConfig',
    'chats.apps.ChatsConfig',
    'crons.apps.CronsConfig',
    'users.apps.UsersConfig',
    'feedback.apps.FeedbackConfig',
    'subscriptions.apps.SubscriptionsConfig',
    'webhooks.apps.WebhooksConfig',
    # Rest Framework Apps
    'rest_framework',
    'rest_framework.authtoken',
    # Channels Pub-Sub
    'channels',
    # Static File Storage
    'storages',
]

REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',  # Logins and Sign Ups only
        'user': '3000/hour',  # Project APIs and Account Info
        'burst': '100/minute',  # User interactions with a Chat App
        'typing': '1/second',  # Is typing requests
    }
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'server.urls'

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

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_USER_MODEL = 'accounts.User'

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Channels & Redis Cache
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("localhost", 6379)],
        },
    },
}
ASGI_APPLICATION = 'server.routing.application'

# Cross Origin Resource Sharing

ALLOWED_HOSTS = ['.herokuapp.com', '127.0.0.1:8000']
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = list(default_headers) + [
    'public-key',
    'project-id',
    'private-key',
    'user-name',
    'user-secret',
    'chat-id',
    'access-key',
]

# Static File Storage
AWS_ACCESS_KEY_ID = get_secret('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = get_secret('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = get_secret('AWS_STORAGE_BUCKET_NAME')

AWS_DEFAULT_ACL = None
AWS_S3_FILE_OVERWRITE = False
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_REGION_NAME = 'ca-central-1'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# TODO: Put AWS_QUERYSTRING_EXPIRE over 3600

# KEEP AT THE END
if get_secret('PIPELINE') == 'production':
    from .production import *
elif get_secret('PIPELINE') == 'proxy':
    from .proxy import *
elif get_secret('PIPELINE') == 'staging':
    from .staging import *
else:
    from .local import *


DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
