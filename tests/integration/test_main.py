#!/usr/bin/env python

import logging

#################################################################################
# Enable logging

log = logging.getLogger('test.main')

#################################################################################

from tests.helpers import GitRepoMainTestCase

class Test_Main(GitRepoMainTestCase):
    log = log
    target = 'hub'

    def test_clone__too_many_slashes(self):
        self.main_clone('guyzmo/git/repo', 2)

    def test_create__no_such_path(self):
        self.main_add('guyzmo/git-repo', 2,
                      {'--path': '/'})

    def test_clone(self):
        self.main_clone('guyzmo/git-repo', 0)

    def test_fork(self):
        self.main_fork('guyzmo/git-repo', 0)

    def test_create(self):
        self.main_create('guyzmo/git-repo', 0)

    def test_delete(self):
        self.main_delete('guyzmo/git-repo', 0)

    def test_delete__no_user(self):
        self.main_delete('git-repo', 0)

    def test_add(self):
        self.main_add('guyzmo/git-repo', 0)

    def test_open(self):
        self.main_open('guyzmo/git-repo', 0)

    def test_noop(self):
        self.main_noop('guyzmo/git-repo', 1)


