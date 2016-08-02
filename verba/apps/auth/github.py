import requests
from urllib.parse import urlencode

from revision.settings import config

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

    return 'https://github.com/login/oauth/authorize?{}'.format(urlencode(params))


def get_token(code):
    """
    Returns the GitHub token from the code GH provides or AuthException in case of errors.
    """
    params = {
        'client_id': config.GITHUB_AUTH.CLIENT_ID,
        'client_secret': config.GITHUB_AUTH.CLIENT_SECRET,
        'code': code
    }

    response = requests.post(
        'https://github.com/login/oauth/access_token',
        data=params,
        headers={'Accept': 'application/json'}
    )

    if not response.ok:
        raise AuthValidationError('Github response was {}'.format(response.status_code))

    json_response = response.json()
    if 'error_description' in json_response:
        raise AuthValidationError(json_response['error_description'])

    return json_response['access_token']


def get_user_data(token):
    """
    Returns the data of the logged in user associated with the token or AuthException in case of errors.
    """
    response = requests.get(
        'https://api.github.com/user',
        headers={
            'Authorization': 'token {}'.format(token)
        }
    )

    if not response.ok:
        raise AuthValidationError('Github response was {}'.format(response.status_code))

    return response.json()
