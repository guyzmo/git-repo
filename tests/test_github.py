#!/usr/bin/env python

from .helpers import TestCase, fmt

import logging
log = logging.getLogger('{red}test.github{reset}'.format(**fmt))

from git import Repo

class TestGithub(TestCase):
    target = 'hub'

    def test_00_github_clone(self):
        log.info(__name__)
        self.api_clone('guyzmo/git-repo')

    def test_01_github_fork_delete(self):
        log.info(__name__)
        self.api_fork('sigmavirus24/github3.py')
        self.api_delete('github3.py')

    def test_02_github_create_delete(self):
        log.info(__name__)
        Repo.init(self.tempdir.name)
        self.api_create('guyzmo/foobar')
        self.api_delete('foobar')

    def test_03_github_create_create_delete(self):
        log.info(__name__)
        Repo.init(self.tempdir.name)
        self.api_create('guyzmo/foobar')
        # check project already exists error
        self.api_create('guyzmo/foobar', rc=2)
        self.api_delete('foobar')

    def test_04_github_delete(self):
        log.info(__name__)
        Repo.init(self.tempdir.name)
        # delete a non-existent remote repository
        self.api_delete('foobar', rc=2)

    def test_05_github_add(self):
        log.info(__name__)
        Repo.init(self.tempdir.name)
        self.api_add('guyzmo/foobar')

    def test_06_github_open(self):
        log.info(__name__)
        Repo.init(self.tempdir.name)
        self.api_open('guyzmo/foobar')

    def test_07_github_noop(self):
        log.info(__name__)
        Repo.init(self.tempdir.name)
        self.api_noop('whatever/whatever')

    def test_08_github_add_error(self):
        log.info(__name__)
        Repo.init(self.tempdir.name)
        self.api_add('foobar', rc=2)


class TestGitlab(TestCase):
    target = 'lab'

    def test_00_gitlab_clone(self):
        log.info(__name__)
        self.api_clone('guyzmo/git-repo')

    def test_01_gitlab_fork_delete(self):
        log.info(__name__)
        self.api_fork('gitlab-org/training-examples')
        self.api_delete('guyzmo/training-examples')

    def test_02_gitlab_create_delete(self):
        log.info(__name__)
        Repo.init(self.tempdir.name)
        self.api_create('guyzmo/foobar')
        self.api_delete('guyzmo/foobar')

    def test_03_gitlab_create_create_delete(self):
        log.info(__name__)
        Repo.init(self.tempdir.name)
        self.api_create('guyzmo/foobar')
        # check project already exists error
        self.api_create('guyzmo/foobar', rc=2)
        self.api_delete('guyzmo/foobar')

    def test_04_gitlab_delete(self):
        log.info(__name__)
        Repo.init(self.tempdir.name)
        # delete a non-existent remote repository
        self.api_delete('guyzmo/barfo', rc=2)

    def test_05_gitlab_add(self):
        log.info(__name__)
        Repo.init(self.tempdir.name)
        self.api_add('guyzmo/foobar')

    def test_06_gitlab_open(self):
        log.info(__name__)
        Repo.init(self.tempdir.name)
        self.api_open('guyzmo/git-repo')

    def test_07_gitlab_noop(self):
        log.info(__name__)
        Repo.init(self.tempdir.name)
        self.api_noop('whatever/whatever')

    def test_08_gitlab_add_error(self):
        log.info(__name__)
        Repo.init(self.tempdir.name)
        self.api_add('foobar', rc=2)


class TestBitBucket(TestCase):
    target = 'bb'

    def test_00_bitbucket_clone(self):
        log.info(__name__)
        self.api_clone('guyzmo/git-repo')

    def test_01_bitbucket_fork_delete(self):
        log.info(__name__)
        self.api_fork('davidzhwang/tutorial-fork-git')
        self.api_delete('tutorial-fork-git')

    def test_02_bitbucket_create_delete(self):
        log.info(__name__)
        Repo.init(self.tempdir.name)
        self.api_create('guyzmo/foobar')
        self.api_delete('foobar')

    def test_03_bitbucket_create_create_delete(self):
        log.info(__name__)
        Repo.init(self.tempdir.name)
        self.api_create('guyzmo/foobar')
        # check project already exists error
        self.api_create('guyzmo/foobar', rc=2)
        self.api_delete('foobar')

    def test_04_bitbucket_delete(self):
        log.info(__name__)
        Repo.init(self.tempdir.name)
        # delete a non-existent remote repository
        self.api_delete('foobar', rc=2)

    def test_05_bitbucket_add(self):
        log.info(__name__)
        Repo.init(self.tempdir.name)
        self.api_add('guyzmo/foobar')

    def test_06_bitbucket_open(self):
        log.info(__name__)
        Repo.init(self.tempdir.name)
        self.api_open('guyzmo/foobar')

    def test_07_bitbucket_noop(self):
        log.info(__name__)
        Repo.init(self.tempdir.name)
        self.api_noop('whatever/whatever')

    def test_08_bitbucket_add_error(self):
        log.info(__name__)
        Repo.init(self.tempdir.name)
        self.api_add('foobar', rc=2)

