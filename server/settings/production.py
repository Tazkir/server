from .base import *

# Security
DEBUG = False

# Database
DB_NAME = get_secret("DB_NAME")
DB_USER_NM = get_secret("DB_USER_NM")
DB_USER_PW = get_secret("DB_USER_PW")
INSTANCE_CONNECTION_NAME = get_secret('INSTANCE_CONNECTION_NAME')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DB_NAME,
        'USER': DB_USER_NM,
        "PASSWORD": DB_USER_PW,
        "HOST": f'/cloudsql/{INSTANCE_CONNECTION_NAME}',
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
