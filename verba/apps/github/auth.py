import requests
from urllib.parse import urlencode

from verba_settings import config

from .exceptions import AuthValidationError


def get_login_url(callback_url=None):
    """
    Returns the GitHub OAuth authorize URL.
    """
    params = {
        'scope': 'public_repo',
        'client_id': config.GITHUB_AUTH.CLIENT_ID,
        'allow_signup': 'false'
    }
    if callback_url:
        params['redirect_uri'] = callback_url

    return '{}/login/oauth/authorize?{}'.format(config.GITHUB_HTTP_HOST, urlencode(params))


def get_token(code):
    """
    Returns the GitHub token from the code GH provides or AuthValidationError in case of errors.
    """
    params = {
        'client_id': config.GITHUB_AUTH.CLIENT_ID,
        'client_secret': config.GITHUB_AUTH.CLIENT_SECRET,
        'code': code
    }

    response = requests.post(
        '{}/login/oauth/access_token'.format(config.GITHUB_HTTP_HOST),
        data=params,
        headers={'Accept': 'application/json'}
    )

    if not response.ok or 'error_description' in response.json():
        raise AuthValidationError.from_response(response)

    return response.json()['access_token']
