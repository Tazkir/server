
from .base import *

# Security
DEBUG = True

PROJECT = os.getenv('PROJECT')

# Database
DB_NAME = get_secret("DB_NAME", project=PROJECT)
DB_USER_NM = get_secret("DB_USER_NM", project=PROJECT)
DB_USER_PW = get_secret("DB_USER_PW", project=PROJECT)
INSTANCE_CONNECTION_IP = get_secret('INSTANCE_CONNECTION_IP', project=PROJECT)
INSTANCE_CONNECTION_PORT = get_secret('INSTANCE_CONNECTION_PORT', project=PROJECT)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DB_NAME,
        'USER': DB_USER_NM,
        "PASSWORD": DB_USER_PW,
        "HOST": INSTANCE_CONNECTION_IP,
        "PORT": INSTANCE_CONNECTION_PORT,
    }
}

# Channels & Redis Cache
REDIS_HOST = get_secret('REDIS_HOST', 'localhost')
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(REDIS_HOST, 6379)],
        },
    },
}
