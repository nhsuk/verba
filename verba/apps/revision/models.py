from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.crypto import get_random_string

from verba_settings import config
import github

from .exceptions import RevisionNotFoundException, RevisionFileNotFoundException


def get_verba_branch_name(revision_id):
    return '{}{}'.format(config.BRANCHES.NAMESPACE, revision_id)


def is_verba_branch(name):
    return name.startswith(config.BRANCHES.NAMESPACE)


def get_revision_id(verba_branch_name):
    if not is_verba_branch(verba_branch_name):
        return None
    return verba_branch_name[len(config.BRANCHES.NAMESPACE):]


def is_content_file(file_name):
    # TODO review
    return file_name.split('.')[-1].lower() == 'md'


class RevisionFile(object):
    def __init__(self, _file, revision_id):
        assert _file.path.startswith(config.PATHS.CONTENT_FOLDER)

        self.revision_id = revision_id
        self._file = _file

    @property
    def name(self):
        return self._file.name

    @property
    def path(self):
        return self._file.path[len(config.PATHS.CONTENT_FOLDER):]

    @property
    def content(self):
        return self._file.content

    def change_content(self, new_content):
        self._file.change_content(
            new_content,
            message='[ci skip] Change file {}'.format(self.path)
        )

    def get_absolute_url(self):
        return reverse('revision:file-detail', args=[self.revision_id, self.path])


class Revision(object):
    def __init__(self, pull, revision_id):
        self.id = revision_id
        self._pull = pull

    @property
    def title(self):
        return self._pull.title

    @property
    def description(self):
        return self._pull.description

    def get_files(self):
        if not hasattr(self, '_files'):
            git_files = self._pull.branch.get_dir_files(config.PATHS.CONTENT_FOLDER)

            self._files = []
            for git_file in git_files:
                if is_content_file(git_file.path):
                    self._files.append(
                        RevisionFile(git_file, self.id)
                    )

        return self._files

    def get_file_by_path(self, path):
        for rev_file in self.get_files():
            if rev_file.path.lower() == path.lower():
                return rev_file
        raise RevisionFileNotFoundException("File '{}' not found".format(path))

    def is_in_progress(self):
        return config.LABELS.IN_PROGRESS in self._pull.labels

    def is_in_review(self):
        return config.LABELS.IN_REVIEW in self._pull.labels

    def mark_as_in_progress(self):
        # get existing labels, remove the 'in review' one and add the 'in progress' one
        labels = list(self._pull.labels)
        if config.LABELS.IN_REVIEW in labels:
            labels.remove(config.LABELS.IN_REVIEW)
        labels.append(config.LABELS.IN_PROGRESS)

        self._pull.labels = labels

    def mark_as_in_review(self):
        # get existing labels, remove the 'in progress' one and add the 'in review' one
        labels = list(self._pull.labels)
        if config.LABELS.IN_PROGRESS in labels:
            labels.remove(config.LABELS.IN_PROGRESS)
        labels.append(config.LABELS.IN_REVIEW)

        self._pull.labels = labels

    def send_for_approval(self, title, description):
        self.mark_as_in_review()
        self._pull.assignees = config.REVIEW_GITHUB_USERS.split(',')
        self._pull.edit(title=title, description=description)

    def delete(self):
        self._pull.close()

    def get_absolute_url(self):
        return reverse('revision:detail', args=[self.id])

    def get_preview_url(self):
        url = config.PREVIEW.URL_GENERATOR(self)
        if not url:
            raise NotImplementedError("Please specify VERBA_CONFIG['PREVIEW']['URL_GENERATOR']")

        return url


class RevisionManager(object):
    def __init__(self, token):
        self._repo = github.Repo(token)

    def get_all(self):
        revisions = []
        for pull in self._repo.get_pulls():
            revision_id = get_revision_id(pull.head_ref)

            if not revision_id:
                continue

            revisions.append(
                Revision(pull, revision_id)
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
        branch = self._repo.create_branch(
            new_branch=branch_name,
            from_branch=config.BRANCHES.BASE
        )

        # create revision log file in log folder
        revision_log_file_path = '{}{}_{}'.format(
            config.PATHS.REVISIONS_LOG_FOLDER,
            timezone.now().strftime('%Y.%m.%d_%H.%M'),
            branch_name
        )

        branch.create_new_file(
            path=revision_log_file_path,
            message='Create revision log file',
            content=''
        )

        # create PR
        pull = self._repo.create_pull(
            title=title,
            body='Content revision {}'.format(title),
            base=config.BRANCHES.BASE,
            head=branch_name
        )

        revision = Revision(pull, revision_id)
        revision.mark_as_in_progress()

        return revision
