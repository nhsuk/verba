import random
import json

from django.core.urlresolvers import reverse
from django.utils import timezone

from github import Repo
from github.exceptions import NotFoundException as GithubNotFoundException

from verba_settings import config

from .utils import is_verba_branch, generate_verba_branch_name, get_verba_branch_name_info, is_content_file
from .constants import REVISION_LOG_FILE_COMMIT_MSG, REVISION_BODY_MSG, CONTENT_FILE_MANIFEST, \
    CONTENT_FILE_INCLUSION_DIRECTIVE, FILE_CHANGED_COMMIT_MSG
from .exceptions import RevisionNotFoundException


def abs_path(path):
    if not path.startswith(config.PATHS.CONTENT_FOLDER):
        return '{}/{}'.format(config.PATHS.CONTENT_FOLDER, path)
    return path


def local_path(path):
    if path.startswith(config.PATHS.CONTENT_FOLDER):
        return path[len(config.PATHS.CONTENT_FOLDER):]
    return path


class RevisionFile(object):
    def __init__(self, _file, revision):
        assert _file.path.startswith(config.PATHS.CONTENT_FOLDER)
        assert _file.path.endswith(CONTENT_FILE_MANIFEST)

        self.revision = revision
        self._file = _file
        self._pull = revision._pull

    @property
    def _file_folder(self):
        return self._file.path.replace(
            '/{}'.format(CONTENT_FILE_MANIFEST), ''
        )

    @property
    def path(self):
        return local_path(self._file_folder)

    def get_content_items(self):
        """
        Returns a dict of items of type (key, value) where:
            - key is the key for the content area
            - value is the actual content
        """
        content = json.loads(self._file.content)

        items = {}
        file_folder = abs_path(self._file_folder)
        for key, value in content.items():
            # if reference to external file for content => load it
            if value.startswith(CONTENT_FILE_INCLUSION_DIRECTIVE):
                filename_to_include = value[len(CONTENT_FILE_INCLUSION_DIRECTIVE):]
                filepath_to_include = '{}/{}'.format(file_folder, filename_to_include)

                git_file = self._pull.branch.get_file(filepath_to_include)
                value = git_file.content

            items[key] = value
        return items

    def save_content_items(self, new_content_items):
        """
        Saves the dict of (key, value) items.
        """
        content = json.loads(self._file.content)

        file_folder = abs_path(self._file_folder)
        for key, old_value in content.items():
            new_value = new_content_items[key]

            # if reference to external file for content => update it
            if old_value.startswith(CONTENT_FILE_INCLUSION_DIRECTIVE):
                filename_to_include = old_value[len(CONTENT_FILE_INCLUSION_DIRECTIVE):]
                filepath_to_include = '{}/{}'.format(file_folder, filename_to_include)

                git_file = self._pull.branch.get_file(filepath_to_include)
                git_file.change_content(
                    new_content=new_value,
                    message=FILE_CHANGED_COMMIT_MSG.format(
                        path=local_path('{}/{}'.format(self.path, filename_to_include))
                    )
                )
            else:
                content[key] = new_value

        # save main manifest
        self._file.change_content(
            json.dumps(content, indent=4),
            message=FILE_CHANGED_COMMIT_MSG.format(path=self.path)
        )

    def get_absolute_url(self):
        return reverse('revision:edit-file', args=[self.revision.id, self.path])

    def get_send_to_2i_url(self):
        return reverse('revision:send-for-2i', args=[self.revision.id])


class Revision(object):
    def __init__(self, pull):
        self._pull = pull

    @property
    def id(self):
        return self._pull.issue_nr

    @property
    def title(self):
        return self._pull.title

    @property
    def statuses(self):
        return list(
            filter(
                lambda label: label in config.LABELS.ALLOWED,
                self._pull.labels
            )
        )

    @property
    def assignees(self):
        return list(
            filter(
                lambda assignee: assignee in config.ASSIGNEES.ALLOWED,
                self._pull.assignees
            )
        )

    @property
    def creator(self):
        _, _, creator, _ = get_verba_branch_name_info(self._pull.head_ref)
        return creator

    def is_in_draft(self):
        return config.LABELS.DRAFT in self.statuses

    def _move_state(self, new_state, new_assignee):
        # labels
        # 1. don't lose any unknown labels
        labels = [label for label in self._pull.labels if label not in config.LABELS.ALLOWED]
        # 2. add only the `new_state` one
        labels.append(new_state)
        # 3. set labels
        self._pull.labels = labels

        # assignees
        # 1. don't lose any unknown assignees
        assignees = [assignee for assignee in self._pull.assignees if assignee not in config.ASSIGNEES.ALLOWED]
        # 2. add only the `new_assignee`
        assignees.append(new_assignee)
        # 3. set assignees
        self._pull.assignees = assignees

    def move_to_draft(self):
        """
        Moves the revision to the draft state, meaning:
        - sets the status to draft
        - sets the assignee to the creator

        This without losing any of the settings that verba does not understand.
        """
        self._move_state(
            new_state=config.LABELS.DRAFT,
            new_assignee=self.creator
        )

    def add_comment(self, comment):
        assert comment
        self._pull.add_comment(comment)

    def move_to_2i(self):
        """
        Moves the revision to the 2i state, meaning:
        - sets the status to 2i
        - sets the assignee to a new random writer

        This without losing any of the settings that verba does not understand.
        """
        # get a random writer
        assignee_list = list(config.ASSIGNEES.ALLOWED)
        assignee_list.remove(self.creator)
        new_assignee = random.choice(assignee_list)

        assert new_assignee, "At least 2 writers required"

        self._move_state(
            new_state=config.LABELS['2I'],
            new_assignee=new_assignee
        )

        return new_assignee

    def get_files(self):
        """
        Returns the list of RevisionFile instances belonging to this revision.
        """
        if not hasattr(self, '_files'):
            git_files = self._pull.branch.get_dir_files(config.PATHS.CONTENT_FOLDER)

            self._files = []
            for git_file in git_files:
                if is_content_file(git_file.path):
                    self._files.append(
                        RevisionFile(git_file, self)
                    )

        return self._files

    def get_file(self, path):
        """
        Return RevisionFile for file with path == `path`.
        """
        full_path = '{}{}/{}'.format(config.PATHS.CONTENT_FOLDER, path, CONTENT_FILE_MANIFEST)
        git_file = self._pull.branch.get_file(full_path)
        return RevisionFile(git_file, self)

    def get_absolute_url(self):
        return reverse('revision:editor', args=[self.id])


class RevisionManager(object):
    def __init__(self, token):
        self._repo = Repo(token)

    def get_all(self):
        """
        Returns only verba revisions.
        """
        revisions = []
        for pull in self._repo.get_pulls():
            if not is_verba_branch(pull.head_ref):
                continue

            revisions.append(
                Revision(pull=pull)
            )
        return revisions

    def get(self, revision_id):
        """
        Returns the Revision with id == `revision_id` or raises RevisionNotFoundException if it doesn't exist.
        """
        try:
            pull = self._repo.get_pull(revision_id)
            if not is_verba_branch(pull.head_ref):
                raise GithubNotFoundException('Not found')
        except GithubNotFoundException:
            raise RevisionNotFoundException('Revision with id {} not found'.format(revision_id))

        return Revision(pull)

    def create(self, title, creator):
        """
        Creates a new revisions meaning:
        - creates a new branch
        - creates an empty file and adds it to the REVISIONS_LOG_FOLDER
        - creates a new PR
        - marks the PR as in draft
        - assigns the PR to the creator
        """
        assert(title and creator)

        # generating branch name
        branch_name = generate_verba_branch_name(title, creator)

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
            message=REVISION_LOG_FILE_COMMIT_MSG,
            content=''
        )

        # create PR
        pull = self._repo.create_pull(
            title=title,
            body=REVISION_BODY_MSG.format(title=title),
            base=config.BRANCHES.BASE,
            head=branch_name
        )

        revision = Revision(pull)
        revision.move_to_draft()

        return revision
