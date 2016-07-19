import github
import base64

from django.conf import settings


def get_repo(token):
    gh = github.Github(login_or_token=token)
    return gh.get_repo(settings.VERBA_GITHUB_REPO)


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
