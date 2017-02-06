#!/usr/bin/env python

import logging

#################################################################################
# Enable logging

log = logging.getLogger('test.gitlab')

#################################################################################

import os
import sys
import pytest

from tests.helpers import GitRepoTestCase

from git_repo.services.service import gitlab
from git_repo.exceptions import ResourceExistsError, ResourceNotFoundError, ResourceError, ArgumentError

class Test_Gitlab(GitRepoTestCase):
    log = log

    @property
    def local_namespace(self):
        if 'GITLAB_NAMESPACE' in os.environ:
            return os.environ['GITLAB_NAMESPACE']
        return 'git-repo-test'

    def get_service(self):
        return gitlab.GitlabService(c=dict())

    def get_requests_session(self):
        return self.service.gl.session

    def test_00_fork(self):
        self.action_fork(local_namespace=self.local_namespace,
                         remote_namespace='sigmavirus24',
                         repository='github3-py')

    def test_01_create__new(self):
        self.action_create(namespace=self.local_namespace,
                           repository='foobar')

    def test_01_create__already_exists(self):
        with pytest.raises(ResourceExistsError):
            self.action_create(namespace=self.local_namespace,
                            repository='git-repo')

    def test_01_create_group__new(self):
        self.action_create(namespace='git-repo-test',
                           repository='foobar')

    def test_01_create_group__already_exists(self):
        with pytest.raises(ResourceExistsError):
            self.action_create(namespace='git-repo-test',
                            repository='git-repo')


    def test_02_delete(self):
        self.action_delete(namespace=self.local_namespace,
                           repository='foobar')

    def test_03_delete_nouser(self):
        self.action_delete(repository='github3-py')

    def test_04_clone(self):
        self.action_clone(namespace='guyzmo',
                          repository='git-repo')

    def test_05_add(self):
        self.action_add(namespace='guyzmo',
                        repository='git-repo')

    def test_06_add__name(self):
        self.action_add(namespace='guyzmo',
                        repository='git-repo',
                        name='test0r')

    def test_07_add__alone(self):
        self.action_add(namespace='guyzmo',
                        repository='git-repo',
                        alone=True)

    def test_08_add__alone_name(self):
        self.action_add(namespace='guyzmo',
                        repository='git-repo',
                        name='test0r',
                        alone=True)

    def test_09_add__default(self):
        self.action_add(namespace='guyzmo',
                        repository='git-repo',
                        tracking='gitlab')

    def test_10_add__default_name(self):
        self.action_add(namespace='guyzmo',
                        repository='git-repo',
                        name='test0r',
                        tracking='gitlab')

    def test_11_add__alone_default(self):
        self.action_add(namespace='guyzmo',
                        repository='git-repo',
                        alone=True,
                        tracking='gitlab')

    def test_12_add__alone_default_name(self):
        self.action_add(namespace='guyzmo',
                        repository='git-repo',
                        alone=True,
                        name='test0r',
                        tracking='gitlab')

    def test_13_snippet_list_alone(self):
        namespace = os.environ.get('GITLAB_NAMESPACE', 'bogus')
        s_list = [
            '{:45.45} {}',
            ("title", "url"),
            ('this is a secret test.', 'https://gitlab.com/snippets/34124',                               ) ,
            ('this is a test.',        'https://gitlab.com/snippets/34121',                               ) ,
            ('this is a test.',        'https://gitlab.com/{}/git-repo/snippets/32318'.format(namespace), ) ,
            ('this is a secret test.', 'https://gitlab.com/{}/git-repo/snippets/32317'.format(namespace), ) ,
            ('this is a test.',        'https://gitlab.com/{}/git-repo/snippets/32316'.format(namespace), ) ,
            ('requirements.txt',       'https://gitlab.com/{}/git-repo/snippets/32303'.format(namespace), ) ,
            ('test',                   'https://gitlab.com/{}/git-repo/snippets/26173'.format(namespace), ) ,
            ('test',                   'https://gitlab.com/snippets/20696',                               )
        ]
        self.action_gist_list(gist_list_data=s_list)

    def test_13_snippet_list_with_project(self):
        self.action_gist_list(gist='guyzmo/git-repo')

    def test_13_snippet_list_with_non_existent_project(self):
        with pytest.raises(ResourceNotFoundError):
            self.action_gist_list(gist='non-existent')

    def test_14_snippet_clone(self):
        with pytest.raises(ArgumentError):
            self.action_gist_clone(gist='XXX')

    def test_15_snippet_fetch_global_snippet(self):
        snippet = self.action_gist_fetch(gist='20696')
        assert snippet == "test"

    def test_15_snippet_fetch_project_snippet(self):
        content = self.action_gist_fetch(gist='https://gitlab.com/guyzmo/git-repo/snippets/32303')
        assert content == '\n'.join([
            'docopt',
            'progress',
            'GitPython>=2.1.0',
            'uritemplate.py==2.0.0',
            'github3.py==0.9.5',
            'python-gitlab>=0.13',
            'bitbucket-api', ''
        ])

    def test_15_snippet_fetch_with_bad_project_snippet(self):
        with pytest.raises(ResourceNotFoundError):
            content = self.action_gist_fetch(gist='https://gitlab.com/guyzmo/git-repo/snippets/42')

    def test_16_snippet_create_snippet_global_file(self, datadir):
        test_file = str(datadir[ 'random-fortune-1.txt' ])
        self.action_gist_create(description='this is a test.',
                gist_files=[ test_file ],
                secret=False)

    def test_16_snippet_create_snippet_project_file(self, datadir):
        test_file = str(datadir[ 'random-fortune-1.txt' ])
        self.action_gist_create(description='this is a test.',
                gist_files=[ 'guyzmo/git-repo', test_file ],
                secret=False)

    def test_16_snippet_create_snippet_file_list(self, datadir):
        with pytest.raises(ArgumentError):
            test_files = [
                    str(datadir[ 'random-fortune-1.txt' ]),
                    str(datadir[ 'random-fortune-2.txt' ]),
                    str(datadir[ 'random-fortune-3.txt' ]),
                    str(datadir[ 'random-fortune-4.txt' ]),
            ]
            self.action_gist_create(description='this is a test.',
                    gist_files=test_files,
                    secret=False)

    def test_16_snippet_create_snippet_dir(self, datadir):
        with pytest.raises(IsADirectoryError):
            test_dir = [
                    str(datadir[ 'a_directory' ]),
            ]
            self.action_gist_create(description='this is a test.',
                    gist_files=test_dir,
                    secret=False)

    def test_16_snippet_create_secret_snippet_global_file(self, datadir):
        test_file = str(datadir[ 'random-fortune-1.txt' ])
        self.action_gist_create(description='this is a secret test.',
                gist_files=[ test_file ],
                secret=True)

    def test_16_snippet_create_secret_snippet_project_file(self, datadir):
        test_file = str(datadir[ 'random-fortune-1.txt' ])
        self.action_gist_create(description='this is a secret test.',
                gist_files=[ 'git-repo', test_file ],
                secret=True)

    def test_16_snippet_create_snippet__file_not_exist(self, datadir):
        with pytest.raises(FileNotFoundError):
            test_dir = [
                    'does_not_exists'
            ]
            self.action_gist_create(description='this is a secret test.',
                    gist_files=test_dir,
                    secret=False)

    def test_17_snippet_project_delete(self):
        self.action_gist_delete(gist='https://gitlab.com/guyzmo/git-repo/snippets/32303')

    def test_17_snippet_project_delete__not_exist(self):
        with pytest.raises(ResourceNotFoundError):
            self.action_gist_delete(gist='https://gitlab.com/guyzmo/git-repo/snippets/32303')

    def test_17_snippet_global_delete(self):
        self.action_gist_delete(gist='https://gitlab.com/snippets/34111')

    def test_17_snippet_global_delete__not_exist(self):
        with pytest.raises(ResourceNotFoundError):
            self.action_gist_delete(gist='https://gitlab.com/snippets/32304')

    def test_18_request_list(self):
        self.action_request_list(
                namespace='git-repo-test',
                repository='git-repo',
                rq_list_data=[
            '{:>3}\t{:<60}\t{:2}',
            ('id', 'title', 'URL'),
            ('1', 'Adding gitlab gists and requests feature', 'https://gitlab.com/git-repo-test/git-repo/merge_requests/1'),
        ])

    def test_19_request_fetch(self):
        self.action_request_fetch(namespace='guyzmo',
                repository='git-repo',
                request='4',
                remote_branch='merge_requests',
                local_branch='requests/gitlab')

    def test_19_request_fetch__bad_request(self):
        with pytest.raises(ResourceNotFoundError):
            self.action_request_fetch(namespace='git-repo-test',
                repository='git-repo',
                request='42',
                remote_branch='merge_requests',
                local_branch='requests/gitlab',
                fail=True)

    def test_20_request_create(self):
        r = self.action_request_create(namespace='guyzmo',
                repository='test_create_requests',
                branch='pr-test',
                title='PR test',
                description='PR description',
                service='gitlab')
        assert r == {'local': 'pr-test', 'ref': 1, 'remote': 'PR test'}

    # TODO lookup why this is not raising the expected error !
    # def test_20_request_create__bad_branch(self):
    #     with pytest.raises(ResourceError):
    #         self.action_request_create(namespace='guyzmo',
    #                 repository='test_create_requests',
    #                 branch='this_is_not_a_branch',
    #                 title='PR test',
    #                 description='PR description',
    #                 service='gitlab')

    def test_20_request_create__bad_repo(self):
        with pytest.raises(ResourceNotFoundError):
            r = self.action_request_create(namespace='guyzmo',
                    repository='does_not_exists',
                    branch='pr-test',
                    title='PR test',
                    description='PR description',
                    service='gitlab')

    def test_20_request_create__blank_branch(self):
        with pytest.raises(ResourceError):
            r = self.action_request_create(namespace='guyzmo',
                    repository='test_create_requests',
                    branch=None,
                    title='PR test',
                    description='PR description',
                    service='gitlab')

    def test_31_open(self):
        self.action_open(namespace='guyzmo',
                         repository='git-repo')

