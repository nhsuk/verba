from django.utils import timezone

from github import Repo

from verba_settings import config

from .utils import is_verba_branch, generate_verba_branch_name, get_verba_branch_name_info
from .constants import REVISION_LOG_FILE_COMMIT_MSG, REVISION_BODY_MSG


class Revision(object):
    def __init__(self, pull, revision_id):
        self.id = revision_id
        self._pull = pull

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
        _, _, creator, _ = get_verba_branch_name_info(self.id)
        return creator

    def move_to_draft(self):
        """
        Moves the revision to the draft state, meaning:
        - sets the status to draft
        - sets the assignee to the creator

        This without losing any of the settings that verba does not understand.
        """
        # labels
        # 1. don't lose any unknown labels
        labels = [label for label in self._pull.labels if label not in config.LABELS.ALLOWED]
        # 2. add only the draft one
        labels.append(config.LABELS.DRAFT)
        # 3. set labels
        self._pull.labels = labels

        # assignees
        # 1. don't lose any unknown assignees
        assignees = [assignee for assignee in self._pull.assignees if assignee not in config.ASSIGNEES.ALLOWED]
        # 2. add only the creator
        assignees.append(self.creator)
        # 3. set assignees
        self._pull.assignees = assignees


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
                Revision(pull=pull, revision_id=pull.head_ref)
            )
        return revisions

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

        revision = Revision(pull, branch_name)
        revision.move_to_draft()

        return revision
