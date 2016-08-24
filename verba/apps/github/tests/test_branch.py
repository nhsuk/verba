import json
import responses

import github
from github.exceptions import InvalidResponseException

from github.tests.test_base import BaseGithubTestCase


class BaseBranchTestCase(BaseGithubTestCase):
    def setUp(self):
        super(BaseBranchTestCase, self).setUp()
        self.path = 'pages/'
        self.branch_name = 'test-branch'
        self.branch = github.Branch(self.TOKEN, self.branch_name)

        self.git_tree_url = self.get_github_api_repo_url('git/trees/{}:{}'.format(self.branch_name, self.path))


class CreateBranchTestCase(BaseBranchTestCase):
    @responses.activate
    def test_success(self):
        responses.add(
            responses.GET, self.get_github_api_repo_url('branches/from-branch'),
            body=self.get_fixture('branch.json'), status=200,
            content_type='application/json'
        )

        responses.add(
            responses.POST, self.get_github_api_repo_url('git/refs'),
            body=self.get_fixture('create_branch.json'), status=201,
            content_type='application/json'
        )

        branch = github.Branch.create(
            token=self.TOKEN,
            new_branch='new-branch',
            from_branch='from-branch'
        )
        self.assertEqual(branch.name, 'new-branch')
        self.assertEqual(branch.token, self.TOKEN)

    @responses.activate
    def test_invalid_new_branch(self):
        responses.add(
            responses.GET, self.get_github_api_repo_url('branches/from-branch'),
            body=self.get_fixture('branch.json'), status=200,
            content_type='application/json'
        )

        responses.add(
            responses.POST, self.get_github_api_repo_url('git/refs'),
            body=json.dumps({
                "documentation_url": "https://developer.github.com/v3/git/refs/#create-a-reference",
                "message": "Reference already exists"
            }), status=422,
            content_type='application/json'
        )

        self.assertRaises(
            InvalidResponseException,
            github.Branch.create,
            token=self.TOKEN,
            new_branch='already-exists',
            from_branch='from-branch'
        )

    @responses.activate
    def test_invalid_from_branch(self):
        responses.add(
            responses.GET, self.get_github_api_repo_url('branches/not-existing'),
            body=json.dumps({
                "documentation_url": "https://developer.github.com/v3/git/refs/#create-a-reference",
                "message": "Branch not found"
            }), status=422,
            content_type='application/json'
        )

        self.assertRaises(
            InvalidResponseException,
            github.Branch.create,
            token=self.TOKEN,
            new_branch='new-branch',
            from_branch='not-existing'
        )


class GetGitTreeTestCase(BaseBranchTestCase):
    @responses.activate
    def test_valid(self):
        responses.add(
            responses.GET, self.git_tree_url,
            body=self.get_fixture('git_tree.json'), status=200,
            content_type='application/json'
        )

        response = self.branch.get_git_tree(path=self.path, recursive=True)
        self.assertTrue('tree' in response)
        self.assertEqual(len(response['tree']), 4)

    @responses.activate
    def test_invalid_path(self):
        responses.add(
            responses.GET, self.git_tree_url,
            body=json.dumps({
                "documentation_url": "https://developer.github.com/v3",
                "message": "Not Found"
            }),
            status=404, content_type='application/json'
        )

        self.assertRaises(
            InvalidResponseException,
            self.branch.get_git_tree,
            path=self.path
        )


class GetDirFilesTestCase(BaseBranchTestCase):
    @responses.activate
    def test_valid(self):
        responses.add(
            responses.GET, self.git_tree_url,
            body=self.get_fixture('git_tree.json'), status=200,
            content_type='application/json'
        )

        files = self.branch.get_dir_files(path=self.path)
        self.assertEqual(len(files), 4)
        for _file in files:
            self.assertTrue(_file.path.startswith(self.path))

    @responses.activate
    def test_invalid(self):
        responses.add(
            responses.GET, self.git_tree_url,
            body=json.dumps({
                "documentation_url": "https://developer.github.com/v3",
                "message": "Not Found"
            }),
            status=404, content_type='application/json'
        )

        self.assertRaises(
            InvalidResponseException,
            self.branch.get_dir_files,
            path=self.path
        )


class GetFileTestCase(BaseBranchTestCase):
    def test_get_file(self):
        path = 'some-path'
        git_file = self.branch.get_file(path)

        self.assertEqual(git_file.token, self.TOKEN)
        self.assertEqual(git_file.path, path)
        self.assertEqual(git_file.branch_name, self.branch.name)
