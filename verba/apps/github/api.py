import json
import requests
import base64
import logging

from django.utils.dateparse import parse_datetime

from verba_settings import config

from .exceptions import InvalidResponseException, NotFoundException


logger = logging.getLogger('github.api')


class Request(object):
    def __init__(self, token):
        self.token = token
        self.url = None

    def _build_url(self, url_part):
        return '{}/{}'.format(config.GITHUB_API_HOST, url_part)

    def set_url(self, url_or_part):
        if not url_or_part.startswith(config.GITHUB_API_HOST):
            self.url = self._build_url(url_or_part)
        else:
            self.url = url_or_part
        return self

    def get(self, params={}):
        return self._make('get', params=params)

    def put(self, data={}):
        return self._make('put', data=json.dumps(data))

    def patch(self, data={}):
        return self._make('patch', data=json.dumps(data))

    def post(self, data={}):
        return self._make('post', data=json.dumps(data))

    def _make(self, verb, **kwargs):
        kwargs['headers'] = {
            'Authorization': 'token {}'.format(self.token),
            'Accept': 'application/json'
        }

        verb_func = getattr(requests, verb)
        logger.debug('{} with URL: {}'.format(verb, self.url))
        response = verb_func(self.url, **kwargs)

        if not response.ok:
            if response.status_code == 404:
                raise NotFoundException.from_response(response)
            raise InvalidResponseException.from_response(response)

        return response.json()


class RepoRequest(Request):
    """
    Like Request but used for actions on a repo.
    """
    def _build_url(self, url_part):
        return '{}/repos/{}/{}'.format(config.GITHUB_API_HOST, config.REPO, url_part)


def abs_path(path):
    if path.startswith('/'):
        return path
    return '/{}'.format(path)


class Comment(object):
    def __init__(self, token, data):
        self.token = token
        self._data = data

    @property
    def body(self):
        return self._data['body']

    @property
    def created_at(self):
        return parse_datetime(self._data['created_at'])

    @property
    def created_by(self):
        return self._data['user']['login']


class File(object):
    def __init__(self, token, path, branch_name):
        self.token = token
        self.path = path
        self.branch_name = branch_name

    @property
    def _data(self):
        if not hasattr(self, '_cached_data'):
            url = 'contents/{}'.format(self.path)
            params = {
                'path': self.path,
                'ref': self.branch_name
            }
            self._cached_data = RepoRequest(self.token).set_url(url).get(params=params)
        return self._cached_data

    @property
    def name(self):
        return self._data['name']

    @property
    def content(self):
        return base64.b64decode(self._data['content']).decode("utf-8")

    @classmethod
    def create_or_update(cls, token, path, branch_name, content, message, update_sha=None):
        encoded_content = base64.b64encode(content.encode('utf-8')).decode("utf-8")
        url = 'contents/{}'.format(path)
        params = {
            'path': path,
            'message': message,
            'content': encoded_content,
            'branch': branch_name
        }

        if update_sha:
            params['sha'] = update_sha

        data = RepoRequest(token).set_url(url).put(data=params)
        return (data, encoded_content)

    def change_content(self, new_content, message):
        content_data, _ = self.create_or_update(
            self.token, self.path, self.branch_name, new_content, message,
            update_sha=self._data['sha']
        )
        setattr(self, '_cached_data', content_data)

    @classmethod
    def create(cls, token, path, branch_name, content, message):
        response_data, encoded_content = cls.create_or_update(
            token, path, branch_name, content, message
        )

        # constructing file / content
        git_file = cls(token=token, path=path, branch_name=branch_name)

        content_data = response_data['content']
        content_data['content'] = encoded_content  # the api don't return this field when creating/updating
        setattr(git_file, '_cached_data', content_data)
        return git_file


class Branch(object):
    def __init__(self, token, name):
        self.token = token
        self.name = name

    def create_new_file(self, path, message, content):
        return File.create(
            self.token, path,
            branch_name=self.name,
            content=content, message=message
        )

    def get_git_tree(self, path, recursive=False):
        sha = '{}:{}'.format(self.name, path)

        url = 'git/trees/{}?recursive={}'.format(
            sha, '1' if recursive else '0'
        )
        return RepoRequest(self.token).set_url(url).get()

    def get_dir_files(self, path):
        tree_data = self.get_git_tree(path, recursive=True)
        return [
            File(self.token, '{}{}'.format(path, tree_el['path']), self.name)
            for tree_el in tree_data['tree']
        ]

    def get_file(self, path):
        # it does not check if the file exists => it's being optimistic to avoid
        # performance penalties.
        # It not ideal, change
        return File(self.token, path, self.name)

    @classmethod
    def create(cls, token, new_branch, from_branch):
        from_branch_data = RepoRequest(token).set_url('branches/{}'.format(from_branch)).get()
        from_branch_sha = from_branch_data['commit']['sha']

        new_branch_ref = 'refs/heads/{}'.format(new_branch)

        data = {
            'ref': new_branch_ref,
            'sha': from_branch_sha
        }
        RepoRequest(token).set_url('git/refs').post(data)
        return cls(token, new_branch)


class PullRequest(object):
    def __init__(self, token, data):
        self.token = token
        self._data = data

    @property
    def branch(self):
        return Branch(self.token, self.head_ref)

    @property
    def issue_nr(self):
        return self._data['number']

    @property
    def issue(self):
        if not hasattr(self, '_issue'):
            issue_data = RepoRequest(self.token).set_url(self._data['issue_url']).get()
            self._issue = Issue(self.token, issue_data)
        return self._issue

    @property
    def title(self):
        return self._data['title']

    @property
    def description(self):
        return self._data['body']

    @property
    def created_at(self):
        return parse_datetime(self._data['created_at'])

    def edit(self, title, description):
        data = {
            'title': title,
            'body': description
        }
        RepoRequest(self.token).set_url(self._data['url']).patch(data)
        self._data['title'] = title
        self._data['body'] = description

    def close(self):
        data = {
            'state': 'closed'
        }
        RepoRequest(self.token).set_url(self._data['url']).patch(data)

    @property
    def head_ref(self):
        return self._data['head']['ref']

    @property
    def labels(self):
        return self.issue.labels

    @labels.setter
    def labels(self, labels):
        self.issue.labels = labels

    @property
    def assignees(self):
        return self.issue.assignees

    @assignees.setter
    def assignees(self, assignees):
        self.issue.assignees = assignees

    def add_comment(self, comment):
        self.issue.add_comment(comment)

    @property
    def comments(self):
        return self.issue.comments

    @property
    def tot_comments(self):
        return self._data['comments']

    @classmethod
    def create(cls, token, title, body, base, head):
        data = {
            'title': title,
            'body': body,
            'head': head,
            'base': base
        }
        pull_data = RepoRequest(token).set_url('pulls').post(data)
        return cls(token, pull_data)

    @classmethod
    def all(cls, token):
        pulls = []
        for pull_data in RepoRequest(token).set_url('pulls').get():
            pulls.append(PullRequest(token, pull_data))
        return pulls

    @classmethod
    def get(cls, token, number):
        pull_data = RepoRequest(token).set_url('pulls/{}'.format(number)).get()
        return cls(token, pull_data)


class Issue(object):
    def __init__(self, token, data):
        self.token = token
        self._data = data

    @property
    def labels(self):
        return [label['name'] for label in self._data['labels']]

    @labels.setter
    def labels(self, labels):
        data = {
            'labels': labels
        }
        pull_data = RepoRequest(self.token).set_url(self._data['url']).patch(data)
        self._data = pull_data

    @property
    def assignees(self):
        return [label['login'] for label in self._data['assignees']]

    @assignees.setter
    def assignees(self, assignees):
        data = {
            'assignees': assignees
        }
        pull_data = RepoRequest(self.token).set_url(self._data['url']).patch(data)
        self._data = pull_data

    def add_comment(self, comment):
        data = {
            'body': comment
        }
        RepoRequest(self.token).set_url(self._data['comments_url']).post(data)

    @property
    def comments(self):
        comments_data = RepoRequest(self.token).set_url(self._data['comments_url']).get()
        return [
            Comment(self.token, data)
            for data in comments_data
        ]


class Repo(object):
    def __init__(self, token):
        self.token = token

    def get_pulls(self):
        return PullRequest.all(self.token)

    def get_pull(self, number):
        return PullRequest.get(self.token, number=number)

    def create_pull(self, title, body, base, head):
        return PullRequest.create(self.token, title, body, base, head)

    def create_branch(self, new_branch, from_branch):
        return Branch.create(self.token, new_branch, from_branch)


class User(object):
    def __init__(self, token, data):
        self.token = token
        self._data = data

    @property
    def username(self):
        return self._data['login']

    @property
    def name(self):
        return self._data['name']

    @property
    def email(self):
        return self._data['email']

    @property
    def avatar_url(self):
        return self._data['avatar_url']

    @classmethod
    def get_logged_in(cls, token):
        user_data = Request(token).set_url('user').get()
        return cls(token, user_data)
