import os
import sys

# PATH vars

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root = lambda *x: os.path.join(BASE_DIR, *x)

sys.path.insert(0, root('apps'))


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'u1fgde|OZSORNfXRkR)te7bQ$!yOMJh+>OdM80Lo1JTn]29q5F'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
IN_TESTING = sys.argv[1:2] == ['test']

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    # 'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles'
]

PROJECT_APPS = [
    'revision',
]

INSTALLED_APPS += PROJECT_APPS

MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'verba.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'verba.wsgi.application'

# Database

DATABASES = {}

# Internationalization

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'Europe/London'

USE_I18N = False

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_ROOT = root('staticfiles')
STATIC_URL = '/static/'


# Additional locations of static files

STATICFILES_DIRS = (
    root('assets'),
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'DIRS': [
            root('templates'),
        ],
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                'django.template.context_processors.static',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    }
]

# Password validation

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


VERBA_GITHUB_TOKEN = None  # GitHub token for access to API
VERBA_CONFIG = {
    'REPO': None,  # GitHub repo with content files to edit in format '<org>/<repo>'
    'PATHS': {
        'CONTENT_FOLDER': 'pages/',  # path to folder containing the content files
        'REVISIONS_LOG_FOLDER': 'content-revision-logs/',  # path to folder that will include revision files
    },
    'BRANCHES': {
        'NAMESPACE': 'content-',  # prefix of the branches that will be created
        'BASE': 'develop',  # base branch for PRs
    },
    'LABELS': {
        'IN_PROGRESS': 'do not merge',  # label to apply for newly created PRs
        'IN_REVIEW': 'for review',  # label to apply for PRs ready for review
    },
    'MAX_REVISIONS': 3,  # max number of revisions allowed
    'REVIEW_GITHUB_USERS': [],  # PR will be assigned to these github usernames when sending a review for approval
    'PREVIEW': {
        'TIMEOUT': 120,  # in secs
        'URL_GENERATOR': lambda rev: None  # lambda generator or the preview url
    }
}

from django.contrib.messages import constants as message_constants
MESSAGE_TAGS = {
    message_constants.DEBUG: '',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'danger',
}


# .local.py overrides all the common settings.
try:
    from .local import *  # noqa
except ImportError:
    pass


# importing test settings file if necessary
if IN_TESTING:
    from .testing import *  # noqa
