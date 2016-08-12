from .base import *  # noqa


VERBA_CONFIG.update({
    'GITHUB_HTTP_HOST': 'https://example.com',
    'GITHUB_API_HOST': 'https://api.example.com',
    'REPO': 'test-owner/test-repo'
})
VERBA_CONFIG['ASSIGNEES']['ALLOWED'] = ['test-owner']
