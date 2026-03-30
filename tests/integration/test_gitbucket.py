#!/usr/bin/env python3

import os
import sys
import logging

import pytest

#################################################################################
# Enable logging

log = logging.getLogger('test.gitbucket')

#################################################################################

from tests.helpers import GitRepoTestCase

from git_repo.services.service import gitbucket
from git_repo.exceptions import ResourceExistsError, ResourceNotFoundError, ResourceError


class Test_Gitbucket(GitRepoTestCase):
    log = log
    namespace = os.environ['GITBUCKET_NAMESPACE']


    @property
    def local_namespace(self):
        if 'GITBUCKET_NAMESPACE' in os.environ:
            return os.environ['GITBUCKET_NAMESPACE']
        return 'git-repo-user'

    def get_service(self):
        return gitbucket.GitbucketService(c={
            '__name__': 'gitrepo "gitbucket"',
            'fqdn': "localhost",
            'port': "8080",
            'scheme': "http",
            'insecure': 'yes',
            'ssh-url': 'ssh://git@localhost:29418'
            })

    def get_requests_session(self):
        return self.service.gh._session

    def test_00_fork(self):
        # AttributeError occurs, because GitBucket doesn't support repos/forks API.
        with pytest.raises(AttributeError):
            self.action_fork(local_namespace=self.local_namespace,
                             remote_namespace='root',
                             repository='repo')

    def test_01_create__new(self):
        self.action_create(namespace=self.local_namespace,
                           repository='foobar')

    def test_01_create__already_exists(self):
        # GitBucket doesn't return 422. it returns 200. maybe GitBucket's issue?
        # with pytest.raises(ResourceExistsError):
        self.action_create(namespace=self.local_namespace,
                        repository='git-repo')

    # skip because GitBucket doesn't support create group's repo by POST /api/v3/users/:org/repos
    @pytest.mark.skip
    def test_01_create_organization__new(self):
        self.action_create(namespace='group',
                           repository='foobar')

    # skip because GitBucket doesn't support create group's repo by POST /api/v3/users/:org/repos
    @pytest.mark.skip
    def test_01_create_organization__already_exists(self):
        with pytest.raises(ResourceExistsError):
            self.action_create(namespace='group',
                            repository='git-repo')

    def test_02_delete(self):
        with pytest.raises(NotImplementedError):
            self.action_delete(namespace=self.local_namespace,
                               repository='foobar')

    def test_03_delete_nouser(self):
        with pytest.raises(NotImplementedError):
            self.action_delete(repository='github3.py')

    def test_04_clone(self):
        self.action_clone(namespace='root',
                          repository='repo')

    def test_05_add(self):
        self.action_add(namespace='root',
                        repository='repo')

    def test_06_add__name(self):
        self.action_add(namespace='root',
                        repository='repo',
                        name='test0r')

    def test_07_add__alone(self):
        self.action_add(namespace='root',
                        repository='repo',
                        alone=True)

    def test_08_add__alone_name(self):
        self.action_add(namespace='root',
                        repository='repo',
                        name='test0r',
                        alone=True)

    def test_09_add__default(self):
        self.action_add(namespace='root',
                        repository='repo',
                        tracking='gitbucket')

    def test_10_add__default_name(self):
        self.action_add(namespace='root',
                        repository='repo',
                        name='test0r',
                        tracking='gitbucket')

    def test_11_add__alone_default(self):
        self.action_add(namespace='root',
                        repository='repo',
                        alone=True,
                        tracking='gitbucket')

    def test_12_add__alone_default_name(self):
        self.action_add(namespace='root',
                        repository='repo',
                        alone=True,
                        name='test0r',
                        tracking='gitbucket')

    def test_13_gist_list(self):
        with pytest.raises(NotImplementedError):
            g_list = []
            self.action_gist_list(gist_list_data=g_list)

    def test_14_gist_list_with_gist(self):
        with pytest.raises(NotImplementedError):
            g_list = [
                "C                 2542  i2c_scanner.c"
            ]
            self.action_gist_list(gist='10118958')

    def test_15_gist_list_with_bad_gist(self):
        with pytest.raises(NotImplementedError):
            self.action_gist_list(gist='42')

    def test_16_gist_clone_with_gist(self):
        with pytest.raises(NotImplementedError):
            self.action_gist_clone(gist='https://gist.github.com/10118958')

    def test_17_gist_fetch_with_gist(self):
        with pytest.raises(NotImplementedError):
            content = self.action_gist_fetch(gist='4170462', gist_file=None)
            assert content == '\n'.join([
                'diff --git a/platform/io.c b/platform/io.c',
                'index 209666a..0a6c2cf 100644',
                '--- a/platform/io.c',
                '+++ b/platform/io.c',
                '@@ -24,6 +24,16 @@',
                ' #if defined(__FreeBSD__)',
                ' #define IO_BSD',
                ' #elif defined(__APPLE__)',
                '+size_t strnlen(const char *s, size_t maxlen) ',
                '+{ ',
                '+        size_t len; ',
                '+ ',
                '+        for (len = 0; len < maxlen; len++, s++) { ',
                '+                if (!*s) ',
                '+                        break; ',
                '+        } ',
                '+        return (len); ',
                '+} ',
                ' #define IO_BSD',
                ' #define IO_USE_SELECT',
                ' #elif defined(WIN32)',
            ])

    def test_18_gist_fetch_with_bad_gist(self):
        with pytest.raises(NotImplementedError):
            self.action_gist_fetch(gist='69', gist_file=None)

    def test_19_gist_fetch_with_gist_file(self):
        with pytest.raises(NotImplementedError):
            content = self.action_gist_fetch(gist='4170462', gist_file='freevpn0.029__platform__io.patch')
            assert content == '\n'.join([
                'diff --git a/platform/io.c b/platform/io.c',
                'index 209666a..0a6c2cf 100644',
                '--- a/platform/io.c',
                '+++ b/platform/io.c',
                '@@ -24,6 +24,16 @@',
                ' #if defined(__FreeBSD__)',
                ' #define IO_BSD',
                ' #elif defined(__APPLE__)',
                '+size_t strnlen(const char *s, size_t maxlen) ',
                '+{ ',
                '+        size_t len; ',
                '+ ',
                '+        for (len = 0; len < maxlen; len++, s++) { ',
                '+                if (!*s) ',
                '+                        break; ',
                '+        } ',
                '+        return (len); ',
                '+} ',
                ' #define IO_BSD',
                ' #define IO_USE_SELECT',
                ' #elif defined(WIN32)',
            ])

    def test_20_gist_fetch_with_bad_gist_file(self):
        with pytest.raises(NotImplementedError):
            self.action_gist_fetch(gist='4170462', gist_file='failed')

    def test_21_gist_create_gist_file(self, datadir):
        with pytest.raises(NotImplementedError):
            test_file = str(datadir[ 'random-fortune-1.txt' ])
            self.action_gist_create(description='this is a test.',
                    gist_files=[ test_file ],
                    secret=False)

    def test_22_gist_create_gist_file_list(self, datadir):
        with pytest.raises(NotImplementedError):
            test_files = [
                    str(datadir[ 'random-fortune-1.txt' ]),
                    str(datadir[ 'random-fortune-2.txt' ]),
                    str(datadir[ 'random-fortune-3.txt' ]),
                    str(datadir[ 'random-fortune-4.txt' ]),
            ]
            self.action_gist_create(description='this is a test.',
                    gist_files=test_files,
                    secret=False)

    def test_23_gist_create_gist_dir(self, datadir):
        with pytest.raises(NotImplementedError):
            test_dir = [
                    str(datadir[ 'a_directory' ]),
            ]
            self.action_gist_create(description='this is a test.',
                    gist_files=test_dir,
                    secret=False)

    def test_24_gist_create_gist_file(self, datadir):
        with pytest.raises(NotImplementedError):
            test_file = str(datadir[ 'random-fortune-1.txt' ])
            self.action_gist_create(description='this is a secret test.',
                    gist_files=[ test_file ],
                    secret=True)

    def test_25_gist_create_gist_file_list(self, datadir):
        with pytest.raises(NotImplementedError):
            test_files = [
                    str(datadir[ 'random-fortune-1.txt' ]),
                    str(datadir[ 'random-fortune-2.txt' ]),
                    str(datadir[ 'random-fortune-3.txt' ]),
                    str(datadir[ 'random-fortune-4.txt' ]),
            ]
            self.action_gist_create(description='this is a secret test.',
                    gist_files=test_files,
                    secret=True)

    def test_26_gist_create_gist_dir(self, datadir):
        with pytest.raises(NotImplementedError):
            test_dir = [
                    str(datadir[ 'a_directory' ]),
            ]
            self.action_gist_create(description='this is a secret test.',
                    gist_files=test_dir,
                    secret=True)

    def test_27_gist_delete(self):
        with pytest.raises(NotImplementedError):
            self.action_gist_delete(gist='7dcc495dda5e684cba94940a01f60e95')

    def test_28_gist_delete__not_exist(self):
        with pytest.raises(NotImplementedError):
            self.action_gist_delete(gist='7dcc495dda5e684cba94940a01f60e95')

    def test_29_gist_create_gist__file_not_exist(self, datadir):
        with pytest.raises(NotImplementedError):
            test_dir = [
                    'does_not_exists'
            ]
            self.action_gist_create(description='this is a secret test.',
                    gist_files=test_dir,
                    secret=False)

    @pytest.mark.skip
    def test_30_request_list(self):
        self.action_request_list(
                namespace='root',
                repository='repo',
                rq_list_data=[
            '{}\t{:<60}\t{}',
            ('id', 'title', 'URL'),
            ('3', 'docs for fqdn > url', 'https://github.com/guyzmo/git-repo/pull/3'),
            ('2', 'prefer gitrepo.<target>.token > privatekey, docs', 'https://github.com/guyzmo/git-repo/pull/2'),
        ])

    @pytest.mark.skip
    def test_31_request_fetch(self):
        self.action_request_fetch(namespace='root',
                repository='repo',
                request='1',
                remote_branch='pull',
                local_branch='requests/gitbucket')

    @pytest.mark.skip
    def test_31_request_fetch__bad_request(self):
        with pytest.raises(ResourceNotFoundError):
            self.action_request_fetch(namespace='guyzmo',
                repository='git-repo',
                request='1',
                remote_branch='pull',
                local_branch='requests/github',
                fail=True)

    @pytest.mark.skip
    def test_32_request_create(self):
        r = self.action_request_create(namespace=self.namespace,
                repository='test_create_requests',
                source_branch='pr-test',
                target_branch='master',
                title='PR test',
                description='PR description')
        assert r == {
                'local': 'pr-test',
                'ref': 1,
                'remote': 'master',
                'url': 'https://github.com/{}/test_create_requests/pull/1'.format(self.namespace),
                }

    @pytest.mark.skip
    def test_32_request_create__bad_branch(self):
        with pytest.raises(ResourceError):
            self.action_request_create(namespace=self.namespace,
                    repository='test_create_requests',
                    source_branch='does_not_exists',
                    target_branch='master',
                    title='PR test',
                    description='PR description')

    @pytest.mark.skip
    def test_32_request_create__bad_repo(self):
        with pytest.raises(ResourceNotFoundError):
            r = self.action_request_create(namespace=self.namespace,
                    repository='does_not_exists',
                    source_branch='pr-test',
                    target_branch='master',
                    title='PR test',
                    description='PR description')

    @pytest.mark.skip
    def test_32_request_create__guess_branch(self):
        r = self.action_request_create(namespace=self.namespace,
                repository='test_create_requests',
                source_branch=None,
                target_branch=None,
                title='PR test',
                description='PR description')

    def test_33_open(self):
        self.action_open(namespace='root',
                         repository='repo')

    @pytest.mark.skip
    def test_34_list__short(self, caplog):
        projects = self.action_list(namespace='group')
        assert projects == ['{}', ('Total repositories: 1',), ['git-repo-test/git-repo']]
        assert 'GET https://api.github.com/users/git-repo-test/repos' in caplog.text

    @pytest.mark.skip
    def test_34_list__long(self, caplog):
        projects = self.action_list(namespace='git-repo-test', _long=True)
        assert projects == ['{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{:12}\t{}',
                ['Status', 'Commits', 'Reqs', 'Issues', 'Forks', 'Coders', 'Watch', 'Likes', 'Lang', 'Modif', 'Name'],
                ['F ', '92', '0', '0', '0', '1', '0', '0', 'Python', 'Mar 30 2016', 'git-repo-test/git-repo']]
        assert 'GET https://api.github.com/users/git-repo-test/repos' in caplog.text


