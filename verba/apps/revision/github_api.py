import github
import base64

from .settings import config


def abs_path(path):
    if path.startswith('/'):
        return path
    return '/{}'.format(path)


def get_repo(token):
    gh = github.Github(login_or_token=token)
    return gh.get_repo(config.REPO)


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


def get_dir_files(repo, path, ref=github.GithubObject.NotSet):
    sha = '{}:{}'.format(ref, path)
    git_tree = repo.get_git_tree(sha, recursive=True)
    return [tree_el.path for tree_el in git_tree.tree]


def get_file_contents(repo, path, ref=github.GithubObject.NotSet):
    return repo.get_file_contents(abs_path(path), ref=ref)


def add_assignees_to_issue(repo, issue_nr, assignees):
    assert isinstance(assignees, list), assignees

    post_parameters = {
        'assignees': assignees
    }
    headers, data = repo._requester.requestJsonAndCheck(
        "POST",
        repo.url + "/issues/" + str(issue_nr) + "/assignees",
        input=post_parameters
    )
