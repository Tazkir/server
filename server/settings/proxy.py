from .base import *

# Security
DEBUG = True
SECRET_KEY = get_secret('SECRET_KEY', 'dd6b99cb-ea3b-4e45-ad63-6792e7f1efec')

# Production
DB_NAME = get_secret("DB_NAME")
DB_USER_NM = get_secret("DB_USER_NM")
DB_USER_PW = get_secret("DB_USER_PW")
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DB_NAME,
        'USER': DB_USER_NM,
        "PASSWORD": DB_USER_PW,
        "HOST": '127.0.0.1',
        "PORT": 6543,
    }
}

# Channels & Redis Cache
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [get_secret('REDIS_URL', 'redis://localhost:6379')],
        },
    },
}
