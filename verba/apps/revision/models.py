import github

from verba_settings import config


def is_verba_branch(name):
    """
    Returns True if the branch `name` is a Verba branch, that is,
    created by Verba.
    """
    return name.startswith(config.BRANCHES.NAMESPACE)


class Revision(object):
    def __init__(self, pull, revision_id):
        self.id = revision_id
        self._pull = pull

    @property
    def title(self):
        return self._pull.title

    @property
    def statuses(self):
        return self._pull.labels


class RevisionManager(object):
    def __init__(self, token):
        self._repo = github.Repo(token)

    def get_all(self):
        revisions = []
        for pull in self._repo.get_pulls():
            if not is_verba_branch(pull.head_ref):
                continue

            revisions.append(
                Revision(pull=pull, revision_id=pull.head_ref)
            )
        return revisions
