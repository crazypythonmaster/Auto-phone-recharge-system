import authorize

DEBUG = True

TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ppars_b',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
    }
}

# Change TEST to PRODUCTION in production
AUTHORIZE_ENVIRONMENT = authorize.Environment.PRODUCTION

BROKER_URL = 'amqp://pparsb:pparsb@localhost:5672/pparsb'

SITE_DOMAIN = 'http://ppars-b.py3pi.com'

# for live server use 'www' for test server use 'sandbox'
USAEPAY_WSDL = "https://www.usaepay.com/soap/gate/CD12CD14/usaepay.wsdl"

# for live server use 'secure' for test server use 'staging'
REDFIN_WSDL = "https://secure.redfinnet.com/admin/ws/recurring.asmx?WSDL"
REDFIN_TRANSACTION_WSDL = "https://secure.redfinnet.com/SmartPayments/transact.asmx?WSDL"

TEST_MODE = False

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/3",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

print(__file__, 'production B', 'loaded')