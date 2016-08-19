from django.utils.text import slugify
from django.utils.crypto import get_random_string

from verba_settings import config

from .constants import BRANCH_PARTS_SEPARATOR, CONTENT_FILE_MANIFEST


def is_verba_branch(name):
    """
    Returns True if the branch `name` is a Verba branch, that is,
    created by Verba.
    """
    namespace, _, _, _ = get_verba_branch_name_info(name)
    return bool(namespace)


def generate_verba_branch_name(title, creator):
    """
    Generates a verba branch name from `title` and `creator`.
    """
    return BRANCH_PARTS_SEPARATOR.join([
        config.BRANCHES.NAMESPACE,
        slugify(title[:10]),
        creator,
        get_random_string(length=10)
    ])


def get_verba_branch_name_info(branch_name):
    """
    Returns a tuple of:
        (namespace, slugified title, creator, random string)
    or
        (None, None, None, None)
    if `branch_name` is not a valid Verba branch
    """
    parts = branch_name.split(BRANCH_PARTS_SEPARATOR)
    if len(parts) != 4 or parts[0] != config.BRANCHES.NAMESPACE:
        return (None, None, None, None)

    return tuple(parts)


def is_content_file(path):
    """
    Returns True if file_name matches the CONTENT_FILE_MANIFEST naming convention
    """
    file_name = path.split('/')[-1]
    return file_name and file_name.lower() == CONTENT_FILE_MANIFEST
