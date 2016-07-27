from .base import *  # noqa
import os


DEBUG = False
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

SECRET_KEY = os.environ["SECRET_KEY"]

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

ADMINS = (
    ('NHS.UK', ''),
)

MANAGERS = ADMINS

MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

VERBA_GITHUB_TOKEN = os.environ["VERBA_GITHUB_TOKEN"]
VERBA_CONFIG['REPO'] = os.environ["VERBA_REPO"]
VERBA_CONFIG['REVIEW_GITHUB_USERS'] = os.environ["VERBA_REVIEW_GITHUB_USERS"]
VERBA_CONFIG['PREVIEW']['URL_GENERATOR'] = \
    lambda rev: os.environ["VERBA_REVIEW_URL_GENERATOR"].format(rev._pull.issue_nr)


SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 300
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
