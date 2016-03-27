#!/usr/bin/env python

import sys
import logging

#################################################################################
# make all debug prefix more readable by colourising them

from tests.helpers import colourise_logger, fmt

colourise_logger(logging.getLogger('github3'), 'cyan')
colourise_logger(logging.getLogger('git.cmd'), 'magenta')
colourise_logger(logging.getLogger('git_repo'), 'green')
colourise_logger(logging.getLogger('git_repo.github'), 'blue')

#################################################################################
# Enable logging

log = logging.getLogger('{red}test.github{reset}'.format(**fmt))

#################################################################################

from tempfile import TemporaryDirectory
from git import Repo

from tests.helpers import GitRepoTestCase

from unittest import TestCase

from git_repo.services.service import github

class Test_Github(GitRepoTestCase):
    log = log

    def get_service(self):
        return github.GithubService(c=dict())

    def get_requests_session(self):
        return self.service.gh._session

    def test_00_fork(self):
        self.action_fork(cassette_name=sys._getframe().f_code.co_name,
                         local_namespace='guyzmo',
                         remote_namespace='sigmavirus24', repository='github3.py')

    def test_01_create(self):
        self.action_create(cassette_name=sys._getframe().f_code.co_name,
                           namespace='guyzmo',
                           repository='foobar')


    def test_02_delete(self):
        self.action_delete(cassette_name=sys._getframe().f_code.co_name,
                           namespace='guyzmo',
                           repository='foobar')

    def test_03_delete_nouser(self):
        self.action_delete(cassette_name=sys._getframe().f_code.co_name,
                           repository='github3.py')

    def test_04_clone(self):
        self.action_clone(cassette_name=sys._getframe().f_code.co_name,
                          namespace='guyzmo',
                          repository='git-repo')

    def test_05_add(self):
        self.action_add(cassette_name=sys._getframe().f_code.co_name,
                        namespace='guyzmo',
                        repository='git-repo')

    def test_06_add__name(self):
        self.action_add(cassette_name=sys._getframe().f_code.co_name,
                        namespace='guyzmo',
                        repository='git-repo',
                        name='test0r')

    def test_07_add__alone(self):
        self.action_add(cassette_name=sys._getframe().f_code.co_name,
                        namespace='guyzmo',
                        repository='git-repo',
                        alone=True)

    def test_08_add__alone_name(self):
        self.action_add(cassette_name=sys._getframe().f_code.co_name,
                        namespace='guyzmo',
                        repository='git-repo',
                        name='test0r',
                        alone=True)

    def test_09_add__default(self):
        self.action_add(cassette_name=sys._getframe().f_code.co_name,
                        namespace='guyzmo',
                        repository='git-repo',
                        tracking='github')

    def test_10_add__default_name(self):
        self.action_add(cassette_name=sys._getframe().f_code.co_name,
                        namespace='guyzmo',
                        repository='git-repo',
                        name='test0r',
                        tracking='github')

    def test_11_add__alone_default(self):
        self.action_add(cassette_name=sys._getframe().f_code.co_name,
                        namespace='guyzmo',
                        repository='git-repo',
                        alone=True,
                        tracking='github')

    def test_12_add__alone_default_name(self):
        self.action_add(cassette_name=sys._getframe().f_code.co_name,
                        namespace='guyzmo',
                        repository='git-repo',
                        alone=True,
                        name='test0r',
                        tracking='github')

    def test_13_open(self):
        self.action_open(cassette_name=sys._getframe().f_code.co_name,
                         namespace='guyzmo',
                         repository='git-repo')


