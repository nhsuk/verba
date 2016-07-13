import github

from django.conf import settings


BRANCH_NAMESPACE = 'content-'


def get_verba_branch_name(revision_name):
    return '{}{}'.format(BRANCH_NAMESPACE, revision_name)


def is_verba_branch(name):
    return name.startswith(BRANCH_NAMESPACE)


def get_revision_name(verba_branch_name):
    return verba_branch_name[len(BRANCH_NAMESPACE):]


class Revision(object):
    def __init__(self, repo, name, pull):
        self.repo = repo
        self.name = name
        self.pull = pull


class RevisionManager(object):
    def __init__(self, token):
        gh = github.Github(login_or_token=token)
        self.repo = gh.get_repo(settings.VERBA_GITHUB_REPO)

    def get_all(self):
        revisions = []
        for pull in self.repo.get_pulls():
            head_ref = pull.head.ref
            if not is_verba_branch(head_ref):
                continue

            name = get_revision_name(head_ref)
            revisions.append(
                Revision(self.repo, name, pull)
            )
        return revisions
