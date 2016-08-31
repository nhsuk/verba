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

VERBA_CONFIG['REPO'] = os.environ["VERBA_REPO"]
VERBA_CONFIG['GITHUB_AUTH'] = {
    'CLIENT_ID': os.environ["VERBA_CLIENT_ID"],
    'CLIENT_SECRET': os.environ["VERBA_CLIENT_SECRET"],
}
VERBA_CONFIG['ASSIGNEES'] = {
    'ALLOWED': os.environ["VERBA_ASSIGNEES_ALLOWED"].split(','),
    'WRITERS': os.environ["VERBA_ASSIGNEES_WRITERS"].split(','),
    'DEVELOPERS': os.environ["VERBA_ASSIGNEES_DEVELOPERS"].split(','),
}


SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 300
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
