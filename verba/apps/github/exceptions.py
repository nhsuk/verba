class GitHubException(Exception):
    pass


class InvalidResponseException(GitHubException):
    def __init__(self, message, reason=None):
        super(InvalidResponseException, self).__init__(message)
        self.reason = reason

    @classmethod
    def from_response(cls, response):
        message = 'Received {} from {}'.format(response.status_code, response.request.url)
        reason = '' if not response.content else response.json()
        return cls(message, reason)


class NotFoundException(InvalidResponseException):
    pass


class AuthValidationError(InvalidResponseException):
    pass
