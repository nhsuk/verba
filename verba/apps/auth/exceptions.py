class AuthException(Exception):
    pass


class Unauthorized(AuthException):
    pass


class AuthValidationError(AuthException):
    pass
