import github
import base64

from .settings import config


def abs_path(path):
    if path.startswith('/'):
        return path
    return '/{}'.format(path)


def create_or_update_file(repo, path, message, content, branch=github.GithubObject.NotSet, update=True):
    assert isinstance(path, str), path
    assert branch is github.GithubObject.NotSet or isinstance(branch, str), branch

    fullpath = abs_path(path)

    post_parameters = {
        'path': fullpath,
        'message': message,
        'content': base64.b64encode(content.encode('utf-8')).decode("utf-8")
    }

    if update:
        gitfile = repo.get_contents(fullpath, ref=branch)
        post_parameters['sha'] = gitfile.sha

    if branch is not github.GithubObject.NotSet:
        post_parameters["branch"] = branch

    headers, data = repo._requester.requestJsonAndCheck(
        "PUT",
        repo.url + "/contents" + fullpath,
        input=post_parameters
    )


def create_file(repo, path, message, content, branch=github.GithubObject.NotSet):
    create_or_update_file(repo, path, message, content, branch=branch, update=False)


def update_file(repo, path, message, content, branch=github.GithubObject.NotSet):
    create_or_update_file(repo, path, message, content, branch=branch, update=True)


class File(object):
    def __init__(self, gh_path, branch):
        self._gh_path = gh_path
        self.branch = branch

    @property
    def _gh_file(self):
        if not hasattr(self, '__gh_file'):
            self.__gh_file = self.branch.repo.get_gh_repo().get_file_contents(self._gh_path, ref=self.branch.name)
        return self.__gh_file

    @property
    def name(self):
        return self._gh_file.name

    @property
    def content(self):
        return self._gh_file.decoded_content

    @property
    def path(self):
        return self._gh_path

    def change_content(self, new_content, message):
        update_file(
            self.branch.repo._gh_repo,
            path=self._gh_path,
            message=message,
            content=new_content,
            branch=self.branch.name
        )


class Branch(object):
    def __init__(self, name, repo):
        self.repo = repo
        self.name = name

    def create_new_file(self, path, message, content):
        create_file(self.repo.get_gh_repo(), path, message, content, branch=self.name)

    def get_git_tree(self, path, recursive=False):
        sha = '{}:{}'.format(self.name, path)
        return self.repo.get_gh_repo().get_git_tree(sha, recursive=True)

    def get_dir_files(self, path):
        git_tree = self.get_git_tree(path, recursive=True)
        return [
            File('{}{}'.format(path, tree_el.path), self)
            for tree_el in git_tree.tree
        ]


class PullRequest(object):
    def __init__(self, gh_pull, repo):
        self.repo = repo
        self._gh_pull = gh_pull

    @property
    def branch(self):
        return Branch(self._gh_pull.head.ref, self.repo)

    @property
    def issue_nr(self):
        return int(self._gh_pull.issue_url.split('/')[-1].strip())

    @property
    def issue(self):
        return self.repo.get_issue(self.issue_nr)

    @property
    def title(self):
        return self._gh_pull.title

    @property
    def description(self):
        return self._gh_pull.body

    def edit(self, title, description):
        self._gh_pull.edit(title=title, body=description)

    @property
    def head_ref(self):
        return self._gh_pull.head.ref

    @property
    def labels(self):
        return self.issue.labels

    @labels.setter
    def labels(self, labels):
        self.issue.labels = labels

    def add_assignees(self, assignees):
        assert isinstance(assignees, list), assignees

        post_parameters = {
            'assignees': assignees
        }

        gh_repo = self.repo.get_gh_repo()
        headers, data = gh_repo._requester.requestJsonAndCheck(
            "POST",
            gh_repo.url + "/issues/" + str(self.issue_nr) + "/assignees",
            input=post_parameters
        )


class Issue(object):
    def __init__(self, gh_issue, repo):
        self._gh_issue = gh_issue
        self.repo = repo

    @property
    def labels(self):
        return [label.name for label in self._gh_issue.get_labels()]

    @labels.setter
    def labels(self, labels):
        self._gh_issue.set_labels(*labels)


class Repo(object):
    def __init__(self, gh_repo):
        self._gh_repo = gh_repo

    def get_gh_repo(self):
        # this is ungly but the pygithub lib wants you to trigger actions from the repository object =>
        # it has to be exposed so that other objects can access it.
        return self._gh_repo

    def get_pulls(self):
        pulls = []
        for gh_pull in self._gh_repo.get_pulls():
            pulls.append(
                PullRequest(gh_pull, self)
            )
        return pulls

    def create_pull(self, title, body, base, head):
        gh_pull = self._gh_repo.create_pull(
            title=title, body=body,
            base=base, head=head
        )

        return PullRequest(gh_pull, self)

    def get_issue(self, nr):
        gh_issue = self._gh_repo.get_issue(nr)
        return Issue(gh_issue, self)

    def create_branch(self, new_branch, from_branch):
        new_branch_ref = 'refs/heads/{}'.format(new_branch)
        from_branch_sha = self._gh_repo.get_branch(from_branch).commit.sha
        self._gh_repo.create_git_ref(new_branch_ref, from_branch_sha)

        return Branch(new_branch, self)


def get_repo(token):
    gh = github.Github(login_or_token=token)
    return Repo(gh.get_repo(config.REPO))
