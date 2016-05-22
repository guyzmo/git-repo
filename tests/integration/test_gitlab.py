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
from git_repo.exceptions import ResourceExistsError

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
        self.action_fork(cassette_name=sys._getframe().f_code.co_name,
                         local_namespace=self.local_namespace,
                         remote_namespace='sigmavirus24',
                         repository='github3-py')

    def test_01_create(self):
        self.action_create(cassette_name=sys._getframe().f_code.co_name,
                           namespace=self.local_namespace,
                           repository='foobar')

    def test_01_create__already_exists(self):
        with pytest.raises(ResourceExistsError):
            self.action_create(cassette_name=sys._getframe().f_code.co_name,
                            namespace=self.local_namespace,
                            repository='git-repo')


    def test_02_delete(self):
        self.action_delete(cassette_name=sys._getframe().f_code.co_name,
                           namespace=self.local_namespace,
                           repository='foobar')

    def test_03_delete_nouser(self):
        self.action_delete(cassette_name=sys._getframe().f_code.co_name,
                           repository='github3-py')

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
                        tracking='gitlab')

    def test_10_add__default_name(self):
        self.action_add(cassette_name=sys._getframe().f_code.co_name,
                        namespace='guyzmo',
                        repository='git-repo',
                        name='test0r',
                        tracking='gitlab')

    def test_11_add__alone_default(self):
        self.action_add(cassette_name=sys._getframe().f_code.co_name,
                        namespace='guyzmo',
                        repository='git-repo',
                        alone=True,
                        tracking='gitlab')

    def test_12_add__alone_default_name(self):
        self.action_add(cassette_name=sys._getframe().f_code.co_name,
                        namespace='guyzmo',
                        repository='git-repo',
                        alone=True,
                        name='test0r',
                        tracking='gitlab')

    def test_13_open(self):
        self.action_open(cassette_name=sys._getframe().f_code.co_name,
                         namespace='guyzmo',
                         repository='git-repo')


