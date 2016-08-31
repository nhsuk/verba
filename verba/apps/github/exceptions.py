import json


class GitHubException(Exception):
    pass


class InvalidResponseException(GitHubException):
    def __init__(self, message, reason=None):
        super(InvalidResponseException, self).__init__(message)
        self.reason = reason

    @classmethod
    def from_response(cls, response):
        message = 'Received {} from {}'.format(response.status_code, response.request.url)
        try:
            reason = response.json()
        except json.decoder.JSONDecodeError:
            reason = ''
        return cls(message, reason)


class NotFoundException(InvalidResponseException):
    pass


class AuthValidationError(InvalidResponseException):
    pass
