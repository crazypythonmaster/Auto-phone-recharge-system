import authorize

# Change TEST to PRODUCTION in production
from .util import root

AUTHORIZE_ENVIRONMENT = authorize.Environment.TEST

# for live server use 'www' for test server use 'sandbox'
USAEPAY_WSDL = "https://sandbox.usaepay.com/soap/gate/0AE595C1/usaepay.wsdl"

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 6000
    }
}

CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

SITE_DOMAIN = 'http://127.0.0.1:8000'

ENCRYPTED_FIELDS_KEYDIR = root('..', 'fieldkeys_dev')

print(__file__, 'local', 'loaded')