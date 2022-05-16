from .base import *

# Security
DEBUG = True
SECRET_KEY = '32eaf9ea-3c39-4107-80da-8060b413a5b5'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
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
