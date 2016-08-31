from .base import *  # noqa


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
}

VERBA_CONFIG.update({
    'GITHUB_HTTP_HOST': 'https://example.com',
    'GITHUB_API_HOST': 'https://api.example.com',
    'REPO': 'test-owner/test-repo'
})
VERBA_CONFIG['ASSIGNEES'] = {
    'ALLOWED': ['test-owner', 'test-owner-2', 'test-developer'],
    'WRITERS': ['test-owner', 'test-owner-2'],
    'DEVELOPERS': ['test-developer']
}
