"""
Django settings for ppars project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""
import os
import djcelery
from .util import root


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'gm2htc2o@oqwm06f))5v(ay-ex7u6hu2)=bfda6pm)o(t#mzx4'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_summernote',

    'djcelery',
    'import_export',
    'south',
    'crispy_forms',

    'ppars.apps.accounts',
    'ppars.apps.card',
    'ppars.apps.charge',
    'ppars.apps.core',
    'ppars.apps.price',
    'ppars.apps.notification',
    'ppars.apps.search',
    'redisboard',
)

# MIDDLEWARE_CLASSES = (
#     # This loads the index definitions, so it has to come first
#     # 'autoload.middleware.AutoloadMiddleware',
#
#     # 'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
#     'django.middleware.cache.UpdateCacheMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.cache.FetchFromCacheMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'gadjo.requestprovider.middleware.RequestProvider',
#     # Uncomment the next line for simple clickjacking protection:
#     # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
# )

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'gadjo.requestprovider.middleware.RequestProvider',
)

ROOT_URLCONF = 'ppars.urls'

WSGI_APPLICATION = 'ppars.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Etc/GMT'

USE_I18N = True

USE_L10N = True

USE_TZ = True

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Host for sending e-mail.
EMAIL_HOST = 'smtp.mandrillapp.com'

# Port for sending e-mail.
EMAIL_PORT = 587

# Optional SMTP authentication information for EMAIL_HOST.
EMAIL_HOST_USER = 'info@ezcloudllc.com'
EMAIL_HOST_PASSWORD = 'UGO7f7wiVF4KLcsAN58C9A'
EMAIL_USE_TLS = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'

#use django selery for task
djcelery.setup_loader()

CELERYBEAT_SCHEDULER = "djcelery.schedulers.DatabaseScheduler"
CELERY_ALWAYS_EAGER = False

CELERY_TIMEZONE = 'UTC'

BROKER_URL = 'amqp://guest:guest@localhost:5672/'
# BROKER_HOST = "localhost"
# BROKER_PORT = 5672
# BROKER_USER = "admin"
# BROKER_PASSWORD = "admin"
# BROKER_VHOST = "vhost"
# CELERY_BACKEND = "amqp"
# CELERY_IMPORTS = ("task", )

SITE_DOMAIN = 'http://ppars-b.py3pi.com'

DEFAULT_FROM_EMAIL = 'no-reply@ppars.com'

SITE_ID = 1


# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = root('static_root')

# Additional locations of static files
STATICFILES_DIRS = (
    root('static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)



# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_DIRS = (
    root('templates'),
)

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/10",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/home/'
LOGOUT_URL = '/logout/'

TEST_MODE = True


# only use the memory file uploader, do not use the file system - not able to do so on
# google app engine
FILE_UPLOAD_HANDLERS = ('django.core.files.uploadhandler.MemoryFileUploadHandler',
                        'django.core.files.uploadhandler.TemporaryFileUploadHandler',
                        )
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440 # the django default: 2.5MB

ENCRYPTED_FIELDS_KEYDIR = root('..', '..', 'fieldkeys')

CRISPY_TEMPLATE_PACK = 'bootstrap3'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(module)s:%(lineno)s] %(message)s",
            'datefmt' : "%Y/%m/%d %H:%M:%S",
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'

        },
        'logfile': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': root('..','logs', 'debug.log'),
            'maxBytes': 500000,
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            #'formatter': 'simple'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'logfile'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django': {
            'handlers': ['console', 'logfile'],
            'propagate': True,
            'level': 'INFO',
        },
        'ppars': {
            'handlers': ['console', 'logfile'],
            'propagate': True,
            'level': 'DEBUG',
        },
    }
}

print(__file__, 'defaults', 'loaded')
