#!/usr/bin/env python

#################################################################################
# make all debug prefix more readable by colourising them

fmt = dict(
    green = '[32m',
    red = '[31m',
    blue = '[35m',
    magenta = '[34m',
    cyan = '[96m',
    reset = '[0m'
)
def colour_name(logger, colour):
    if not 'git_repo' in logger.name:
        logger.name = 'git_repo.{}'.format(logger.name)
    format_name = '{'+colour+'}{}{reset}'
    logger.name = format_name.format(logger.name, **fmt)

colour_name(logging.getLogger('github3'), 'cyan')
colour_name(logging.getLogger('git.cmd'), 'magenta')
colour_name(logging.getLogger('git_repo', 'green')
colour_name(logging.getLogger('git_repo.github', 'blue')

#################################################################################
# Enable logging

import logging
log = logging.getLogger('{red}test.github{reset}'.format(**fmt))

#################################################################################

from tempfile import TemporaryDirectory
from git import Repo

import betamax

from unittest import TestCase

from git_repo.services.service import github

class Test_Github(TestCase):
    def setUp(self):
        log.info(__name__)
        self.tempdir = TemporaryDirectory()
        # repository mockup (in a temporary place)
        self.repository = Repo.init(self.tempdir.name)
        # when initiating service with no repository, the connection is not triggered
        self.service = github.GithubService(c=dict())
        self.service.repository = self.repository
        self.recorder = betamax.Betamax(self.service.gh._session)

    def tearDown(self):
        log.info(__name__)
        self.tempdir.cleanup()

    def assert_added_remote(self, remote):
        try:
            self.repository.remote(remote)
        except ValueError as err:
            raise AssertionError("Remote {} not in repository".format(remote))

    def assert_added_remote_defaults(self):
        self.assert_added_remote('github')
        self.assert_added_remote('all')

    def test_00_fork(self):
        with self.recorder.use_cassette('test_github_00_fork'):
            self.service.connect()
            self.service.fork('sigmavirus24', 'github3.py')
            #
            self.assertIsNotNone(self.service.gh.repository('guyzmo', 'github3.py'),
                                 "Fork not found on github")
            self.assert_added_remote_defaults()


    def test_01_create(self):
        with self.recorder.use_cassette('test_github_01_create'):
            self.service.connect()
            self.service.create('guyzmo', 'foobar')
            #
            self.assertIsNotNone(self.service.gh.repository('guyzmo', 'foobar'),
                                 "Remote repository foobar' not found on github")
            self.assert_added_remote_defaults()

    def test_02_delete(self):
        with self.recorder.use_cassette('test_github_02_delete'):
            self.service.connect()
            self.service.delete(user='guyzmo', repo='foobar')
            self.assertIsNone(self.service.gh.repository('guyzmo', 'foobar'),
                              "Repository 'guyzmo/foobar' not deleted from github")

    def test_03_delete_nouser(self):
        with self.recorder.use_cassette('test_github_03_delete_nouser'):
            self.service.delete(repo='github3.py')
            self.assertIsNone(self.service.gh.repository('guyzmo', 'github3.py'),
                              "Repository 'guyzmo/github3.py' not deleted from github")


    def test_04_clone(self):
        with self.recorder.use_cassette('test_github_04_clone'):
            self.service.connect()
            self.service.clone('guyzmo', 'git-repo')
            #
            self.assert_added_remote_defaults()

    def test_05_add(self):
        with self.recorder.use_cassette('test_github_05_add'):
            # init git in the repository's destination
            self.repository.init()
            self.service.connect()
            self.service.add(user='guyzmo', repo='git-repo')
            #
            self.assert_added_remote_defaults()

    def test_06_add__name(self):
        with self.recorder.use_cassette('test_github_06_add__name'):
            # init git in the repository's destination
            self.repository.init()
            self.service.connect()
            self.service.add(user='guyzmo', repo='git-repo', name='test0r')
            #
            self.assert_added_remote('test0r')
            self.assert_added_remote('all')

    def test_07_add__alone(self):
        with self.recorder.use_cassette('test_github_07_add__alone'):
            # init git in the repository's destination
            self.repository.init()
            self.service.connect()
            self.service.add(user='guyzmo', repo='alone-repo', alone=True)
            self.assert_added_remote('github')
            with self.assertRaises(ValueError) as cm:
                self.repository.remote('all')
                self.assertEquals(ValueError,
                                cm.exception,
                                msg='Remote "all" setup in git repository, whereas it should not')

    def test_08_add__alone_name(self):
        with self.recorder.use_cassette('test_github_08_add__alone_name'):
            # init git in the repository's destination
            self.repository.init()
            self.service.connect()
            self.service.add(user='guyzmo', repo='git-repo', name='test0r')
            #
            self.assert_added_remote('test0r')
            with self.assertRaises(ValueError) as cm:
                self.repository.remote('github')
                self.assertEquals(ValueError,
                                cm.exception,
                                msg='Remote "github" setup in git repository, whereas it should not')
            with self.assertRaises(ValueError) as cm:
                self.repository.remote('all')
                self.assertEquals(ValueError,
                                cm.exception,
                                msg='Remote "all" setup in git repository, whereas it should not')


    def test_09_add__default(self):
        with self.recorder.use_cassette('test_github_09_add__default'):
            # init git in the repository's destination
            self.repository.init()
            self.service.connect()
            self.service.add(user='guyzmo', repo='default-repo', default=True)
            #
            self.assert_added_remote_defaults()
            self.assertTrue(
                'github' in self.repository.branches[0].tracking_branch().name,
                'Could not set "github" as tracking branch master'
            )

    def test_10_add__default_name(self):
        with self.recorder.use_cassette('test_github_10_add__default_name'):
            # init git in the repository's destination
            self.repository.init()
            self.service.connect()
            self.service.add(user='guyzmo', repo='default-repo', default=True, name='test0r')
            #
            self.assertTrue(
                'test0r' in self.repository.branches[0].tracking_branch().name,
                'Could not set "test0r" as tracking branch master'
            )
            self.assert_added_remote('test0r')
            with self.assertRaises(ValueError) as cm:
                self.repository.remote('github')
                self.assertEquals(ValueError,
                                cm.exception,
                                msg='Remote "github" setup in git repository, whereas it should not')
            with self.assertRaises(ValueError) as cm:
                self.repository.remote('all')
                self.assertEquals(ValueError,
                                cm.exception,
                                msg='Remote "all" setup in git repository, whereas it should not')

    def test_11_add__alone_default(self):
        with self.recorder.use_cassette('test_github_11_add__alone_default'):
            # init git in the repository's destination
            self.repository.init()
            self.service.connect()
            self.service.add(user='guyzmo', repo='alone-repo', alone=True, default=True)
            self.assert_added_remote('github')
            self.assertTrue(
                'github' in self.repository.branches[0].tracking_branch().name,
                'Could not set "github" as tracking branch master'
            )
            with self.assertRaises(ValueError) as cm:
                self.repository.remote('all')
                self.assertEquals(ValueError,
                                cm.exception,
                                msg='Remote "all" setup in git repository, whereas it should not')

    def test_12_add__alone_default_name(self):
        with self.recorder.use_cassette('test_github_12_add__alone_default_name'):
            # init git in the repository's destination
            self.repository.init()
            self.service.connect()
            self.service.add(user='guyzmo', repo='alone-repo',
                             alone=True,
                             default=True,
                             name='test0r')
            #
            self.assert_added_remote('test0r')
            with self.assertRaises(ValueError) as cm:
                self.repository.remote('github')
                self.assertEquals(ValueError,
                                cm.exception,
                                msg='Remote "github" setup in git repository, whereas it should not')
            with self.assertRaises(ValueError) as cm:
                self.repository.remote('all')
                self.assertEquals(ValueError,
                                cm.exception,
                                msg='Remote "all" setup in git repository, whereas it should not')
            self.assertTrue(
                'github' in self.repository.branches[0].tracking_branch().name,
                'Could not set "github" as tracking branch master'
            )
            with self.assertRaises(ValueError) as cm:
                self.repository.remote('all')
                self.assertEquals(ValueError,
                                cm.exception,
                                msg='Remote "all" setup in git repository, whereas it should not')

    def test_13_open(self):
        pass
        #with self.recorder.use_cassette('test_github_13_open):

