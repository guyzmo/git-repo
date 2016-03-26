#!/usr/bin/env python

import logging

#################################################################################
# make all debug prefix more readable by colourising them

from tests.helpers import colourise_logger, fmt

colourise_logger(logging.getLogger('gitlab'), 'cyan')
colourise_logger(logging.getLogger('git.cmd'), 'magenta')
colourise_logger(logging.getLogger('git_repo'), 'green')
colourise_logger(logging.getLogger('git_repo.gitlab'), 'blue')

#################################################################################
# Enable logging

log = logging.getLogger('{red}test.gitlab{reset}'.format(**fmt))

#################################################################################

from tests.helpers import GitRepoTestCase

from git_repo.services.service import gitlab

# monkey patch requests with session
from requests import Session
gitlab.gitlab.requests = Session()

class Test_Gitlab(GitRepoTestCase):
    log = log

    def get_service(self):
        return gitlab.GitlabService(c=dict())

    def get_requests_session(self):
        return gitlab.gitlab.requests

    def test_00_fork(self):
        self.action_fork(cassette_name=__name__,
                         local_namespace='guyzmo',
                         remote_namespace='sigmavirus24',
                         repository='github3-py')

    def test_01_create(self):
        self.action_create(cassette_name=__name__,
                           namespace='guyzmo',
                           repository='foobar')


    def test_02_delete(self):
        self.action_delete(cassette_name=__name__,
                           namespace='guyzmo',
                           repository='foobar')

    def test_03_delete_nouser(self):
        self.action_delete(cassette_name=__name__,
                           repository='github3-py')

    def test_04_clone(self):
        self.action_clone(cassette_name=__name__,
                          namespace='guyzmo',
                          repository='git-repo')

    def test_05_add(self):
        self.action_add(cassette_name=__name__,
                        namespace='guyzmo',
                        repository='git-repo')

    def test_06_add__name(self):
        self.action_add(cassette_name=__name__,
                        namespace='guyzmo',
                        repository='git-repo',
                        name='test0r')

    def test_07_add__alone(self):
        self.action_add(cassette_name=__name__,
                        namespace='guyzmo',
                        repository='git-repo',
                        alone=True)

    def test_08_add__alone_name(self):
        self.action_add(cassette_name=__name__,
                        namespace='guyzmo',
                        repository='git-repo',
                        name='test0r',
                        alone=True)

    def test_09_add__default(self):
        self.action_add(cassette_name=__name__,
                        namespace='guyzmo',
                        repository='git-repo',
                        default=True)

    def test_10_add__default_name(self):
        self.action_add(cassette_name=__name__,
                        namespace='guyzmo',
                        repository='git-repo',
                        name='test0r',
                        default=True)

    def test_11_add__alone_default(self):
        self.action_add(cassette_name=__name__,
                        namespace='guyzmo',
                        repository='git-repo',
                        alone=True,
                        default=True)

    def test_12_add__alone_default_name(self):
        self.action_add(cassette_name=__name__,
                        namespace='guyzmo',
                        repository='git-repo',
                        alone=True,
                        name='test0r',
                        default=True)

    def test_13_open(self):
        self.action_open(cassette_name=__name__,
                         namespace='guyzmo',
                         repository='git-repo')


