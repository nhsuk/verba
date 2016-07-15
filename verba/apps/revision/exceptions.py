class RevisionException(Exception):
    pass


class RevisionNotFoundException(RevisionException):
    pass


class RevisionFileNotFoundException(RevisionException):
    pass
