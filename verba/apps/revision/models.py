import github
import base64

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.crypto import get_random_string

from .exceptions import RevisionNotFoundException, RevisionFileNotFoundException

CONTENT_PATH = 'pages/'
REVISIONS_LOG_FOLDER = 'content-revision-logs/'
BRANCH_NAMESPACE = 'content-'
BASE_BRANCH = 'develop'

LABEL_IN_PROGRESS = 'do not merge'
LABEL_IN_REVIEW = 'for review'


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


def create_or_update_file(repo, path, message, content, branch=github.GithubObject.NotSet, update=True):
    assert isinstance(path, str), path
    assert branch is github.GithubObject.NotSet or isinstance(branch, str), branch
    post_parameters = {
        'path': path,
        'message': message,
        'content': base64.b64encode(content.encode('utf-8')).decode("utf-8")
    }

    if update:
        gitfile = repo.get_contents(path, ref=branch)
        post_parameters['sha'] = gitfile.sha

    if branch is not github.GithubObject.NotSet:
        post_parameters["branch"] = branch

    headers, data = repo._requester.requestJsonAndCheck(
        "PUT",
        repo.url + "/contents" + path,
        input=post_parameters
    )


def create_file(repo, path, message, content, branch=github.GithubObject.NotSet):
    create_or_update_file(repo, path, message, content, branch=branch, update=False)


def update_file(repo, path, message, content, branch=github.GithubObject.NotSet):
    create_or_update_file(repo, path, message, content, branch=branch, update=True)


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
    def _issue(self):
        issue_id = int(self.pull.issue_url.split('/')[-1].strip())
        return self.repo.get_issue(issue_id)

    @property
    def branch_name(self):
        return get_verba_branch_name(self.name)

    @property
    def short_title(self):
        return self.pull.title

    @property
    def description(self):
        return self.pull.body

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

    def mark_as_in_progress(self):
        # get existing labels, remove the 'in review' one and add the 'in progress' one
        labels = [l.name for l in self._issue.get_labels()]
        if LABEL_IN_REVIEW in labels:
            labels.remove(LABEL_IN_REVIEW)
        labels.append(LABEL_IN_PROGRESS)

        self._issue.set_labels(*labels)

    def mark_as_in_review(self):
        # get existing labels, remove the 'in progress' one and add the 'in review' one
        labels = [l.name for l in self._issue.get_labels()]
        if LABEL_IN_PROGRESS in labels:
            labels.remove(LABEL_IN_PROGRESS)
        labels.append(LABEL_IN_REVIEW)

        self._issue.set_labels(*labels)

    def send_for_approval(self, title, description):
        self.mark_as_in_review()
        self.pull.edit(title=title, body=description)

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

    def create(self, title):
        # generating branch name
        name = '{}-{}'.format(slugify(title[:10]), get_random_string(length=10))
        branch_name = get_verba_branch_name(name)

        # create branch
        branch_ref = 'refs/heads/{}'.format(branch_name)
        sha = self.repo.get_branch(BASE_BRANCH).commit.sha
        self.repo.create_git_ref(branch_ref, sha)

        # create revision log file in log folder
        revision_log_file_path = abs_path(
            '{}{}_{}'.format(
                REVISIONS_LOG_FOLDER,
                timezone.now().strftime('%Y.%m.%d_%H.%M'),
                branch_name
            )
        )
        create_file(
            self.repo,
            path=revision_log_file_path,
            message='Create revision log file',
            content='',
            branch=branch_name
        )

        # create PR
        pull = self.repo.create_pull(
            title=title,
            body='Content revision {}'.format(title),
            base=BASE_BRANCH,
            head=branch_name
        )

        revision = Revision(self.repo, name, pull)
        revision.mark_as_in_progress()

        return revision
