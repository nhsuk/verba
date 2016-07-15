import github
import base64

from django.conf import settings
from django.core.urlresolvers import reverse

from .exceptions import RevisionNotFoundException, RevisionFileNotFoundException

CONTENT_PATH = 'pages/'
BRANCH_NAMESPACE = 'content-'


def abs_path(path):
    if path.startswith('/'):
        return path
    return '/{}'.format(path)


def get_verba_branch_name(revision_name):
    return '{}{}'.format(BRANCH_NAMESPACE, revision_name)


def is_verba_branch(name):
    return name.startswith(BRANCH_NAMESPACE)


def get_revision_name(verba_branch_name):
    return verba_branch_name[len(BRANCH_NAMESPACE):]


def update_file(repo, path, message, content, branch=github.GithubObject.NotSet):
    gitfile = repo.get_contents(path, ref=branch)

    assert isinstance(path, str), path
    assert branch is github.GithubObject.NotSet or isinstance(branch, str), branch
    post_parameters = {
        'path': path,
        'message': message,
        'content': base64.b64encode(content.encode('utf-8')).decode("utf-8"),
        'sha': gitfile.sha
    }
    if branch is not github.GithubObject.NotSet:
        post_parameters["branch"] = branch

    headers, data = repo._requester.requestJsonAndCheck(
        "PUT",
        repo.url + "/contents" + path,
        input=post_parameters
    )


class RevisionFile(object):
    def __init__(self, repo, revision_name, gitfile):
        assert gitfile.path.startswith(CONTENT_PATH)

        self.repo = repo
        self.revision_name = revision_name
        self.gitfile = gitfile

    @property
    def branch_name(self):
        return get_verba_branch_name(self.revision_name)

    @property
    def name(self):
        return self.gitfile.name

    @property
    def path(self):
        return self.gitfile.path[len(CONTENT_PATH):]

    @property
    def content(self):
        return self.gitfile.decoded_content

    def change_content(self, new_content):
        update_file(
            self.repo,
            path=abs_path(self.gitfile.path),
            message='[ci skip] Change file {}'.format(self.path),
            content=new_content,
            branch=self.branch_name
        )

    def get_absolute_url(self):
        return reverse('revision:file-detail', args=[self.revision_name, self.path])


class Revision(object):
    def __init__(self, repo, name, pull):
        self.repo = repo
        self.name = name
        self.pull = pull

    @property
    def branch_name(self):
        return get_verba_branch_name(self.name)

    @property
    def short_title(self):
        return self.pull.title

    def is_content_file(self, file_name):
        # TODO review
        return file_name.split('.')[-1].lower() == 'md'

    def get_files(self):
        gitfiles = self.repo.get_dir_contents(
            abs_path(CONTENT_PATH), self.branch_name
        )

        files = []
        for gitfile in gitfiles:
            if self.is_content_file(gitfile.name):
                files.append(
                    RevisionFile(self.repo, self.name, gitfile)
                )

        return files

    def get_file_by_path(self, path):
        rev_files = self.get_files()
        for rev_file in rev_files:
            if rev_file.path.lower() == path.lower():
                return rev_file
        raise RevisionFileNotFoundException("File '{}' not found".format(path))

    def get_absolute_url(self):
        return reverse('revision:detail', args=[self.name])


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

    def get_by_name(self, name):
        revisions = self.get_all()
        for revision in revisions:
            if revision.name == name:
                return revision

        raise RevisionNotFoundException("Revision '{}' not found".format(name))
