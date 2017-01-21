#!/usr/bin/env python

import logging

#################################################################################
# Enable logging

log = logging.getLogger('test.gogs')

#################################################################################

import os
import sys
import pytest

from tests.helpers import GitRepoTestCase

from git_repo.services.service import gogs
from git_repo.exceptions import ResourceExistsError

class Test_Gogs(GitRepoTestCase):
    log = log
    fqdn = 'http://127.0.0.1:3000'

    @property
    def local_namespace(self):
        if 'GOGS_NAMESPACE' in os.environ:
            return os.environ['GOGS_NAMESPACE']
        return 'git-repo-test'

    def get_service(self):
        gogs.GogsService.fqdn = self.fqdn
        return gogs.GogsService(c=dict())
        # return gogs.GogsService(c=dict(fqdn=self.fqdn,__name__='gitrepo "gogs"',token=os.environ['PRIVATE_KEY_GOGS']))

    def get_requests_session(self):
        return self.service.session

    def test_00_fork(self):
        pass
        #self.action_fork(local_namespace=self.local_namespace,
        #                 remote_namespace='sigmavirus24',
        #                 repository='github3-py')

    def test_01_create__new(self):
        self.action_create(namespace=self.local_namespace,
                           repository='foobar')

    def test_01_create__already_exists(self):
        with pytest.raises(ResourceExistsError):
            self.action_create(namespace=self.local_namespace,
                            repository='git-repo')

    def test_01_create_group__new(self):
        self.action_create(namespace='guyzmo',
                           repository='foobar')

    def test_01_create_group__already_exists(self):
        with pytest.raises(ResourceExistsError):
            self.action_create(namespace='guyzmo',
                            repository='git-repo')


    def test_02_delete(self):
        self.action_delete(namespace='guyzmo',
                           repository='foobar')

    def test_03_delete_nouser(self):
        self.action_delete(repository='foobar')

    def test_04_clone(self):
        self.action_clone(namespace=self.local_namespace,
                          repository='git-repo')

    def test_05_add(self):
        self.action_add(namespace=self.local_namespace,
                        repository='git-repo')

    def test_06_add__name(self):
        self.action_add(namespace=self.local_namespace,
                        repository='git-repo',
                        name='test0r')

    def test_07_add__alone(self):
        self.action_add(namespace=self.local_namespace,
                        repository='git-repo',
                        alone=True)

    def test_08_add__alone_name(self):
        self.action_add(namespace=self.local_namespace,
                        repository='git-repo',
                        name='test0r',
                        alone=True)

    def test_09_add__default(self):
        self.action_add(namespace=self.local_namespace,
                        repository='git-repo',
                        tracking='gogs')

    def test_10_add__default_name(self):
        self.action_add(namespace=self.local_namespace,
                        repository='git-repo',
                        name='test0r',
                        tracking='gogs')

    def test_11_add__alone_default(self):
        self.action_add(namespace=self.local_namespace,
                        repository='git-repo',
                        alone=True,
                        tracking='gogs')

    def test_12_add__alone_default_name(self):
        self.action_add(namespace=self.local_namespace,
                        repository='git-repo',
                        alone=True,
                        name='test0r',
                        tracking='gogs')

    def test_13_open(self):
        self.action_open(namespace=self.local_namespace,
                         repository='git-repo')


