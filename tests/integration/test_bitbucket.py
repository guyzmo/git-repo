#!/usr/bin/env python

import logging

#################################################################################
# Enable logging

log = logging.getLogger('test.bitbucket')

#################################################################################

import os
import sys
import pytest

from tests.helpers import GitRepoTestCase

from git_repo.services.service import bitbucket
from git_repo.exceptions import ResourceNotFoundError, ResourceError

class Test_BitBucket(GitRepoTestCase):
    log = log

    @property
    def local_namespace(self):
        if 'BITBUCKET_NAMESPACE' in os.environ:
            return os.environ['BITBUCKET_NAMESPACE']
        return 'git-repo-test'

    def get_service(self):
        service = bitbucket.BitbucketService(c=dict())
        return service

    def get_requests_session(self):
        return self.service.bb.client.session

    def test_00_fork(self):
        self.action_fork(local_namespace=self.local_namespace,
                        remote_namespace='abdo2015',
                        repository='git_tutorial')

    def test_01_create(self):
        self.action_create(namespace=self.local_namespace,
                           repository='foobar')


    def test_02_delete(self):
        self.action_delete(namespace=self.local_namespace,
                           repository='foobar')

    def test_03_delete_nouser(self):
        self.action_delete(repository='git_tutorial')

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
                        tracking='bitbucket')

    def test_10_add__default_name(self):
        self.action_add(namespace='guyzmo',
                        repository='git-repo',
                        name='test0r',
                        tracking='bitbucket')

    def test_11_add__alone_default(self):
        self.action_add(namespace='guyzmo',
                        repository='git-repo',
                        alone=True,
                        tracking='bitbucket')

    def test_12_add__alone_default_name(self):
        self.action_add(namespace='guyzmo',
                        repository='git-repo',
                        alone=True,
                        name='test0r',
                        tracking='bitbucket')

    def test_13_snippet_list(self):
        s_list = [
            ('https://bitbucket.org/snippets/guyzmo/ggd4X', 'test'),
            ('https://bitbucket.org/snippets/guyzmo/ggda9', 'test2'),
            ('https://bitbucket.org/snippets/guyzmo/77gaA', 'test3'),
        ]
        self.action_gist_list(gist_list_data=s_list)

    def test_14_snippet_list_with_gist(self):
        g_list = [
            'N.A.                  0 aoeu1.txt',
            'N.A.                  0 aeou2.txt',
        ]
        self.action_gist_list(gist='ggd4X')

    def test_15_snippet_list_with_bad_gist(self):
        with pytest.raises(ResourceNotFoundError):
            self.action_gist_list(gist='42')

    def test_16_snippet_clone_with_gist(self):
        self.action_gist_clone(
            gist='https://bitbucket.org/snippets/{}/ggd4X'.format(os.environ.get('BITBUCKET_NAMESPACE', 'error')),
            clone_url='ssh://git@bitbucket.org/snippets/{}/ggd4X/test'.format(os.environ.get('BITBUCKET_NAMESPACE', 'error'))
        )

    def test_17_snippet_fetch_with_gist(self):
        content = self.action_gist_fetch(gist='77gaA', gist_file=None)
        assert content == '\n'.join([ 'ttt' ])

    def test_18_snippet_fetch_with_bad_gist(self):
        with pytest.raises(ResourceNotFoundError):
            self.action_gist_fetch(gist='69', gist_file=None)

    def test_19_snippet_fetch_with_gist_file(self):
        content = self.action_gist_fetch(gist='ggd4X', gist_file='aoeu1.txt')
        assert content == '\n'.join([ '1' ])

    def test_20_snippet_fetch_with_bad_gist_file(self):
        with pytest.raises(ResourceNotFoundError):
            self.action_gist_fetch(gist='ggd4X', gist_file='failed')

    def test_21_snippet_create_gist_file(self, datadir):
        test_file = str(datadir[ 'random-fortune-1.txt' ])
        self.action_gist_create(description='this is a test.',
                gist_files=[ test_file ],
                secret=False)

    def test_22_snippet_create_gist_file_list(self, datadir):
        test_files = [
                str(datadir[ 'random-fortune-1.txt' ]),
                str(datadir[ 'random-fortune-2.txt' ]),
                str(datadir[ 'random-fortune-3.txt' ]),
                str(datadir[ 'random-fortune-4.txt' ]),
        ]
        self.action_gist_create(description='this is a test.',
                gist_files=test_files,
                secret=False)

    def test_23_snippet_create_gist_dir(self, datadir):
        test_dir = [
                str(datadir[ 'a_directory' ]),
        ]
        self.action_gist_create(description='this is a test.',
                gist_files=test_dir,
                secret=False)

    def test_24_snippet_create_gist_file(self, datadir):
        test_file = str(datadir[ 'random-fortune-1.txt' ])
        self.action_gist_create(description='this is a secret test.',
                gist_files=[ test_file ],
                secret=True)

    def test_25_snippet_create_gist_file_list(self, datadir):
        test_files = [
                str(datadir[ 'random-fortune-1.txt' ]),
                str(datadir[ 'random-fortune-2.txt' ]),
                str(datadir[ 'random-fortune-3.txt' ]),
                str(datadir[ 'random-fortune-4.txt' ]),
        ]
        self.action_gist_create(description='this is a secret test.',
                gist_files=test_files,
                secret=True)

    def test_26_snippet_create_gist_dir(self, datadir):
        test_dir = [
                str(datadir[ 'a_directory' ]),
        ]
        self.action_gist_create(description='this is a secret test.',
                gist_files=test_dir,
                secret=True)

    def test_27_snippet_delete(self):
        self.action_gist_delete(gist='p4RzX')

    def test_28_snippet_delete__not_exist(self):
        with pytest.raises(ResourceNotFoundError):
            self.action_gist_delete(gist='p4RzX')

    def test_29_snippet_create_snippet__file_not_exist(self, datadir):
        with pytest.raises(FileNotFoundError):
            test_dir = [
                    'does_not_exists'
            ]
            self.action_gist_create(description='this is a secret test.',
                    gist_files=test_dir,
                    secret=False)

    def test_30_request_list(self):
        self.action_request_list(
                namespace='atlassian',
                repository='python-bitbucket',
                rq_list_data=[
            ('1', 'Bugfixes for two crashes appearing during reply parsing of repository_create (output of this command is different from normal status, unfortunately). The latter appeared after I fixed the former.', 'https://bitbucket.org/atlassian/python-bitbucket/pull-requests/1'),
            ('2', 'Attempt to fix bitbucket_create crash again, this time py3k compatible', 'https://bitbucket.org/atlassian/python-bitbucket/pull-requests/2'),
            ('3', '[WIP] Initial support for webhooks', 'https://bitbucket.org/atlassian/python-bitbucket/pull-requests/3'),
            ('4', 'fix: lookups for PRs based on state were calling a non existant method', 'https://bitbucket.org/atlassian/python-bitbucket/pull-requests/4'),
            ('5', '🚧 Fork feature implementation', 'https://bitbucket.org/atlassian/python-bitbucket/pull-requests/5'),
            ('6', '💄 Updated code style to be closer to python3 style', 'https://bitbucket.org/atlassian/python-bitbucket/pull-requests/6'),
        ])

    def test_30_request_list_empty(self):
        self.action_request_list(
                namespace='guyzmo',
                repository='git-repo',
                rq_list_data=[ ])

    # TODO
    # def test_31_request_fetch(self):
    #     self.action_request_fetch(namespace='atlassian',
    #             repository='python-bitbucket',
    #             request='2')

    # def test_31_request_fetch__bad_request(self):
    #     with pytest.raises(ResourceNotFoundError):
    #         self.action_request_fetch(namespace='atlassian',
    #             repository='python-bitbucket',
    #             request='42',
    #             fail=True)

    def test_32_request_create__good(self):
        r = self.action_request_create(namespace='guyzmo',
                repository='test_create_requests',
                source_branch='pr-test',
                target_branch='master',
                title='PR test',
                description='PR description')
        assert r == {'local': 'pr-test', 'ref': '1', 'remote': 'master'}

    def test_32_request_create__bad_branch(self):
        with pytest.raises(ResourceNotFoundError):
            self.action_request_create(namespace='guyzmo',
                    repository='test_create_requests',
                    source_branch='does_not_exists',
                    target_branch='master',
                    title='PR test',
                    description='PR description')

    def test_32_request_create__bad_repo(self):
        with pytest.raises(ResourceNotFoundError):
            r = self.action_request_create(namespace='guyzmo',
                    repository='does_not_exists',
                    source_branch='pr-test',
                    target_branch='master',
                    title='PR test',
                    description='PR description')

    def test_32_request_create__guess_branch(self):
        r = self.action_request_create(namespace='guyzmo',
                repository='test_create_requests',
                source_branch=None,
                target_branch=None,
                title='PR test',
                description='PR description')
        assert r == {'local': 'pr-test', 'ref': '1', 'remote': 'master'}

    def test_33_open(self):
        self.action_open(namespace='guyzmo',
                         repository='git-repo')

    def test_34_list__short(self, capsys, caplog):
        import http.client
        http.client.HTTPConnection.debuglevel = 0
        self.action_list(namespace='git-repo-test')
        out, err = capsys.readouterr()
        assert out ==  'git-repo-test/git-repo\n'

    def test_34_list__long(self, capsys, caplog):
        import http.client
        http.client.HTTPConnection.debuglevel = 0
        self.action_list(namespace='git-repo-test', _long=True)
        out, err = capsys.readouterr()
        assert err.replace('\t', ' ') == "Status Commits Reqs Issues Forks Coders Watch Likes Lang Modif  Name\n"
        assert out.replace('\t', ' ') ==  "F  92 1 N.A. 1 N.A. 1 N.A. python 2016-03-30T13:30:15.637449+00:00 git-repo-test/git-repo\n"


