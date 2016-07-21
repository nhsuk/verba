from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.crypto import get_random_string

from .github_api import get_repo, create_file, update_file, get_dir_files, get_file_contents
from .exceptions import RevisionNotFoundException, RevisionFileNotFoundException
from .settings import config


def get_verba_branch_name(revision_id):
    return '{}{}'.format(config.BRANCHES.NAMESPACE, revision_id)


def is_verba_branch(name):
    return name.startswith(config.BRANCHES.NAMESPACE)


def get_revision_id(verba_branch_name):
    if not is_verba_branch(verba_branch_name):
        return None
    return verba_branch_name[len(config.BRANCHES.NAMESPACE):]


class RevisionFile(object):
    def __init__(self, repo, git_path, revision_id, gitfile=None):
        assert git_path.startswith(config.PATHS.CONTENT_FOLDER)

        self.revision_id = revision_id
        self._git_path = git_path
        self._repo = repo
        self.__gitfile = gitfile

    @property
    def _gitfile(self):
        if not self.__gitfile:
            self.__gitfile = get_file_contents(self._repo, self._git_path, self.branch_name)
        return self.__gitfile

    @property
    def branch_name(self):
        return get_verba_branch_name(self.revision_id)

    @property
    def name(self):
        return self._gitfile.name

    @property
    def path(self):
        return self._git_path[len(config.PATHS.CONTENT_FOLDER):]

    @property
    def content(self):
        return self._gitfile.decoded_content

    def change_content(self, new_content):
        update_file(
            self._repo,
            path=self._gitfile.path,
            message='[ci skip] Change file {}'.format(self.path),
            content=new_content,
            branch=self.branch_name
        )

    def get_absolute_url(self):
        return reverse('revision:file-detail', args=[self.revision_id, self.path])


class Revision(object):
    def __init__(self, repo, revision_id, pull):
        self.id = revision_id
        self._repo = repo
        self._pull = pull

    @property
    def _issue_nr(self):
        return int(self._pull.issue_url.split('/')[-1].strip())

    @property
    def _issue(self):
        return self._repo.get_issue(self._issue_nr)

    @property
    def branch_name(self):
        return get_verba_branch_name(self.id)

    @property
    def title(self):
        return self._pull.title

    @property
    def description(self):
        return self._pull.body

    def is_content_file(self, file_name):
        # TODO review
        return file_name.split('.')[-1].lower() == 'md'

    def get_files(self):
        filepaths = get_dir_files(self._repo, config.PATHS.CONTENT_FOLDER, self.branch_name)

        files = []
        for filepath in filepaths:
            if self.is_content_file(filepath):
                git_path = '{}{}'.format(config.PATHS.CONTENT_FOLDER, filepath)
                files.append(
                    RevisionFile(self._repo, git_path, self.id)
                )

        return files

    def get_file_by_path(self, path):
        rev_files = self.get_files()
        for rev_file in rev_files:
            if rev_file.path.lower() == path.lower():
                return rev_file
        raise RevisionFileNotFoundException("File '{}' not found".format(path))

    @property
    def labels(self):
        return [label.name for label in self._issue.get_labels()]

    @labels.setter
    def labels(self, labels):
        self._issue.set_labels(*labels)

    def is_in_progress(self):
        return config.LABELS.IN_PROGRESS in self.labels

    def is_in_review(self):
        return config.LABELS.IN_REVIEW in self.labels

    def mark_as_in_progress(self):
        # get existing labels, remove the 'in review' one and add the 'in progress' one
        labels = list(self.labels)
        if config.LABELS.IN_REVIEW in labels:
            labels.remove(config.LABELS.IN_REVIEW)
        labels.append(config.LABELS.IN_PROGRESS)

        self.labels = labels

    def mark_as_in_review(self):
        # get existing labels, remove the 'in progress' one and add the 'in review' one
        labels = list(self.labels)
        if config.LABELS.IN_PROGRESS in labels:
            labels.remove(config.LABELS.IN_PROGRESS)
        labels.append(config.LABELS.IN_REVIEW)

        self.labels = labels

    def send_for_approval(self, title, description):
        self.mark_as_in_review()
        self._pull.edit(title=title, body=description)

    def get_absolute_url(self):
        return reverse('revision:detail', args=[self.id])

    def get_preview_url(self):
        url = config.PREVIEW.URL_GENERATOR(self)
        if not url:
            raise NotImplementedError("Please specify VERBA_CONFIG['PREVIEW']['URL_GENERATOR']")

        return url


class RevisionManager(object):
    def __init__(self, token):
        self._repo = get_repo(token)

    def get_all(self):
        revisions = []
        for pull in self._repo.get_pulls():
            revision_id = get_revision_id(pull.head.ref)

            if not revision_id:
                continue

            revisions.append(
                Revision(self._repo, revision_id, pull)
            )
        return revisions

    def get_by_id(self, revision_id):
        revisions = self.get_all()
        for revision in revisions:
            if revision.id == revision_id:
                return revision

        raise RevisionNotFoundException("Revision '{}' not found".format(revision_id))

    def create(self, title):
        # generating branch name
        revision_id = '{}-{}'.format(slugify(title[:10]), get_random_string(length=10))
        branch_name = get_verba_branch_name(revision_id)

        # create branch
        branch_ref = 'refs/heads/{}'.format(branch_name)
        sha = self._repo.get_branch(config.BRANCHES.BASE).commit.sha
        self._repo.create_git_ref(branch_ref, sha)

        # create revision log file in log folder
        revision_log_file_path = '{}{}_{}'.format(
            config.PATHS.REVISIONS_LOG_FOLDER,
            timezone.now().strftime('%Y.%m.%d_%H.%M'),
            branch_name
        )

        create_file(
            self._repo,
            path=revision_log_file_path,
            message='Create revision log file',
            content='',
            branch=branch_name
        )

        # create PR
        pull = self._repo.create_pull(
            title=title,
            body='Content revision {}'.format(title),
            base=config.BRANCHES.BASE,
            head=branch_name
        )

        revision = Revision(self._repo, revision_id, pull)
        revision.mark_as_in_progress()

        return revision
