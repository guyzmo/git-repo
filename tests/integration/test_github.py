#!/usr/bin/env python

import os
import sys
import logging

import pytest

#################################################################################
# Enable logging

log = logging.getLogger('test.github')

#################################################################################

from tests.helpers import GitRepoTestCase

from git_repo.services.service import github
from git_repo.exceptions import ResourceExistsError, ResourceNotFoundError, ResourceError


class Test_Github(GitRepoTestCase):
    log = log
    namespace = os.environ['GITHUB_NAMESPACE']

    @property
    def local_namespace(self):
        if 'GITHUB_NAMESPACE' in os.environ:
            return os.environ['GITHUB_NAMESPACE']
        return 'git-repo-test'

    def get_service(self):
        return github.GithubService(c=dict())

    def get_requests_session(self):
        return self.service.gh._session

    def test_00_fork(self):
        self.action_fork(local_namespace=self.local_namespace,
                         remote_namespace='sigmavirus24',
                         repository='github3.py')

    def test_01_create__new(self):
        self.action_create(namespace=self.local_namespace,
                           repository='foobar')

    def test_01_create__already_exists(self):
        with pytest.raises(ResourceExistsError):
            self.action_create(namespace=self.local_namespace,
                            repository='git-repo')

    def test_01_create_organization__new(self):
        self.action_create(namespace='test-git-repo',
                           repository='foobar')

    def test_01_create_organization__already_exists(self):
        with pytest.raises(ResourceExistsError):
            self.action_create(namespace='test-git-repo',
                            repository='git-repo')


    def test_02_delete(self):
        self.action_delete(namespace=self.local_namespace,
                           repository='foobar')

    def test_03_delete_nouser(self):
        self.action_delete(repository='github3.py')

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
                        tracking='github')

    def test_10_add__default_name(self):
        self.action_add(namespace='guyzmo',
                        repository='git-repo',
                        name='test0r',
                        tracking='github')

    def test_11_add__alone_default(self):
        self.action_add(namespace='guyzmo',
                        repository='git-repo',
                        alone=True,
                        tracking='github')

    def test_12_add__alone_default_name(self):
        self.action_add(namespace='guyzmo',
                        repository='git-repo',
                        alone=True,
                        name='test0r',
                        tracking='github')

    def test_13_gist_list(self):
        g_list = [
            '{:45.45} {}',
            ("title", "url"),
            ("unicode combined class for better character counting and indexing",           "https://gist.github.com/a7ce4fddba7744ddf335" ) ,
            ("avr-gcc derivation build",                                                    "https://gist.github.com/7e5a12bc158a79966020" ) ,
            ("avr-gcc derivation",                                                          "https://gist.github.com/dd9ab22c8f22a5a8f3d1" ) ,
            ("`brew cask install mplabx` fixed",                                            "https://gist.github.com/893fbc98bf1c9cf6212a" ) ,
            ("`brew cask install mplabx` issue with target in /usr/local/mplabx",           "https://gist.github.com/9baed8712a16a29c2e90" ) ,
            ("cask formula for mplabx (stripped down)",                                     "https://gist.github.com/1c03ddfdc8f57fa7919a" ) ,
            ("`brew cask install mplabx` issue removing the caskroom dir!",                 "https://gist.github.com/21949a3fa5f981a869bf" ) ,
            ("cask formula for mplabx",                                                     "https://gist.github.com/588deedefc1675998bbe" ) ,
            ("TaskJuggler example",                                                         "https://gist.github.com/281502e4ae6fce01db92" ) ,
            ("redmine to taskjuggler recursive func",                                       "https://gist.github.com/06c5b0da8d10c514166f" ) ,
            ("Simple example of Flask/Presst with Login and Principals (not working!)",     "https://gist.github.com/603ccdd0f504c63cd0df" ) ,
            ("radial colour picker crash",                                                  "https://gist.github.com/2482962b153ebd5cfa6b" ) ,
            ("Platform levelling GCode file",                                               "https://gist.github.com/fc46896f3e604269ff93" ) ,
            ("Code to download movies from pluzz",                                          "https://gist.github.com/3b18193d6bea07bac37c" ) ,
            ("",                                                                            "https://gist.github.com/c01613d0453df275622a" ) ,
            ("I2C scanner code for SL030",                                                  "https://gist.github.com/10118958"             ) ,
            ("",                                                                            "https://gist.github.com/5b79437ddd3f49491ce3" ) ,
            ("An enhanced implementation of authenticating to stackoverflow using python.", "https://gist.github.com/5730750"              ) ,
            ("Patch to be applied for homebrew's strigi.rb Formula.",                       "https://gist.github.com/4308707"              ) ,
            ("Patch for strnlen support in freevpn (for OSX 10.6)",                         "https://gist.github.com/4170462"              ) ,
            ("z.sh patch for multiline quotes",                                             "https://gist.github.com/3666086"              ) ,
            ("A Tornado-based library that enables Event Source support !",                 "https://gist.github.com/2788003"              ) ,
        ]
        self.action_gist_list(gist_list_data=g_list)

    def test_14_gist_list_with_gist(self):
        g_list = [
            "C                 2542  i2c_scanner.c"
        ]
        self.action_gist_list(gist='10118958')

    def test_15_gist_list_with_bad_gist(self):
        self.action_gist_list(gist='42')

    def test_16_gist_clone_with_gist(self):
        self.action_gist_clone(gist='https://gist.github.com/10118958')

    def test_17_gist_fetch_with_gist(self):
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
        with pytest.raises(ResourceNotFoundError):
            self.action_gist_fetch(gist='69', gist_file=None)

    def test_19_gist_fetch_with_gist_file(self):
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
        with pytest.raises(ResourceNotFoundError):
            self.action_gist_fetch(gist='4170462', gist_file='failed')

    def test_21_gist_create_gist_file(self, datadir):
        test_file = str(datadir[ 'random-fortune-1.txt' ])
        self.action_gist_create(description='this is a test.',
                gist_files=[ test_file ],
                secret=False)

    def test_22_gist_create_gist_file_list(self, datadir):
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
        test_dir = [
                str(datadir[ 'a_directory' ]),
        ]
        self.action_gist_create(description='this is a test.',
                gist_files=test_dir,
                secret=False)

    def test_24_gist_create_gist_file(self, datadir):
        test_file = str(datadir[ 'random-fortune-1.txt' ])
        self.action_gist_create(description='this is a secret test.',
                gist_files=[ test_file ],
                secret=True)

    def test_25_gist_create_gist_file_list(self, datadir):
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
        test_dir = [
                str(datadir[ 'a_directory' ]),
        ]
        self.action_gist_create(description='this is a secret test.',
                gist_files=test_dir,
                secret=True)

    def test_27_gist_delete(self):
        self.action_gist_delete(gist='7dcc495dda5e684cba94940a01f60e95')

    def test_28_gist_delete__not_exist(self):
        with pytest.raises(ResourceNotFoundError):
            self.action_gist_delete(gist='7dcc495dda5e684cba94940a01f60e95')

    def test_29_gist_create_gist__file_not_exist(self, datadir):
        with pytest.raises(FileNotFoundError):
            test_dir = [
                    'does_not_exists'
            ]
            self.action_gist_create(description='this is a secret test.',
                    gist_files=test_dir,
                    secret=False)

    def test_30_request_list(self):
        self.action_request_list(
                namespace='guyzmo',
                repository='git-repo',
                rq_list_data=[
            '{}\t{:<60}\t{}',
            ('id', 'title', 'URL'),
            ('3', 'docs for fqdn > url', 'https://github.com/guyzmo/git-repo/pull/3'),
            ('2', 'prefer gitrepo.<target>.token > privatekey, docs', 'https://github.com/guyzmo/git-repo/pull/2'),
        ])

    def test_31_request_fetch(self):
        self.action_request_fetch(namespace='guyzmo',
                repository='git-repo',
                request='2',
                remote_branch='pull',
                local_branch='requests/github')

    def test_31_request_fetch__bad_request(self):
        with pytest.raises(ResourceNotFoundError):
            self.action_request_fetch(namespace='guyzmo',
                repository='git-repo',
                request='1',
                remote_branch='pull',
                local_branch='requests/github',
                fail=True)

    def test_32_request_create(self):
        r = self.action_request_create(namespace=self.namespace,
                repository='test_create_requests',
                branch='pr-test',
                title='PR test',
                description='PR description',
                service='github')
        assert r == {
                'local': 'pr-test',
                'ref': 1,
                'remote': 'PR test',
                'url': 'https://github.com/{}/test_create_requests/pull/1'.format(self.namespace),
                }

    def test_32_request_create__bad_branch(self):
        with pytest.raises(ResourceError):
            self.action_request_create(namespace=self.namespace,
                    repository='test_create_requests',
                    branch='does_not_exists',
                    title='PR test',
                    description='PR description',
                    service='github')

    def test_32_request_create__bad_repo(self):
        with pytest.raises(ResourceNotFoundError):
            r = self.action_request_create(namespace=self.namespace,
                    repository='does_not_exists',
                    branch='pr-test',
                    title='PR test',
                    description='PR description',
                    service='github')

    def test_32_request_create__guess_branch(self):
        r = self.action_request_create(namespace=self.namespace,
                repository='test_create_requests',
                branch=None,
                title='PR test',
                description='PR description',
                service='github')

    def test_33_open(self):
        self.action_open(namespace='guyzmo',
                         repository='git-repo')

    def test_34_list__short(self, caplog):
        projects = self.action_list(namespace='git-repo-test')
        assert projects == ['{}', 'Total repositories: 1', ['git-repo-test/git-repo']]
        assert 'GET https://api.github.com/users/git-repo-test/repos' in caplog.text

    def test_34_list__long(self, caplog):
        projects = self.action_list(namespace='git-repo-test', _long=True)
        assert projects == ['{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t\t{}',
                ['Status', 'Commits', 'Reqs', 'Issues', 'Forks', 'Coders', 'Watch', 'Likes', 'Lang', 'Modif', 'Name'],
                ['F ', '92', '0', '0', '0', '1', '0', '0', 'Python', 'Mar 30 2016', 'git-repo-test/git-repo']]
        assert 'GET https://api.github.com/users/git-repo-test/repos' in caplog.text


