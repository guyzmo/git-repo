#!/usr/bin/env python

fmt = dict(
    green = '[32m',
    red = '[31m',
    blue = '[35m',
    magenta = '[34m',
    cyan = '[96m',
    reset = '[0m'
)
def colourise_logger(logger, colour):
    if not 'git_repo' in logger.name:
        logger.name = 'git_repo.{}'.format(logger.name)
    format_name = '{'+colour+'}{}{reset}'
    logger.name = format_name.format(logger.name, **fmt)

from tempfile import TemporaryDirectory
from unittest import TestCase
from git import Repo
import betamax

class GitRepoTestCase(TestCase):
    def setUp(self):
        self.log.info(__name__)
        self.tempdir = TemporaryDirectory()
        # repository mockup (in a temporary place)
        self.repository = Repo.init(self.tempdir.name)
        # when initiating service with no repository, the connection is not triggered
        self.service = self.get_service()
        self.service.repository = self.repository
        self.recorder = betamax.Betamax(self.get_requests_session())

    def assert_added_remote(self, remote):
        try:
            self.repository.remote(remote)
        except ValueError as err:
            raise AssertionError("Remote {} not in repository".format(remote))

    def assert_added_remote_defaults(self):
        self.assert_added_remote(self.service.name)
        self.assert_added_remote('all')

    '''test cases templates'''

    def action_fork(self, cassette_name, local_namespace, remote_namespace, repository):
        with self.recorder.use_cassette('_'.join(['test', self.service.name, cassette_name])):
            self.service.connect()
            self.service.fork(local_namespace, repository)
            #
            self.assertIsNotNone(self.service.gh.repository(remote_namespace, repository),
                                 "Fork not found on {}".format(self.service.name))
            self.assert_added_remote_defaults()


    def action_create(self, cassette_name, namespace, repository):
        with self.recorder.use_cassette('_'.join(['test', self.service.name, cassette_name])):
            self.service.connect()
            self.service.create(namespace, repository)
            #
            self.assertIsNotNone(self.service.gh.repository(namespace, repository),
                                 "Remote repository {} not found on {}".format(
                                     repository,
                                     self.service.name
                                 ))
            self.assert_added_remote_defaults()

    def action_delete(self, cassette_name, repository, namespace=None):
        with self.recorder.use_cassette('_'.join(['test', self.service.name, cassette_name])):
            self.service.connect()
            if namespace:
                self.service.delete(user=namespace, repo=repository)
            else:
                self.service.delete(repo=repository)
            #
            if not namespace:
                # TODO make a method in repositoryservice that returns current user
                namespace = 'guyzmo'
            self.assertIsNone(self.service.gh.repository(namespace, repository),
                              "Repository '{}' not deleted from {}".format(
                                  '/'.join([namespace, repository]) if namespace else repository,
                                  self.service.name
                              ))

    def action_clone(self, cassette_name, namespace, repository):
        with self.recorder.use_cassette('_'.join(['test', self.service.name, cassette_name])):
            self.service.connect()
            self.service.clone(namespace, repository)
            #
            self.assert_added_remote_defaults()

    def action_add(self, cassette_name, namespace, repository, alone=False, name=None, default=False):
        with self.recorder.use_cassette('_'.join(['test', self.service.name, cassette_name])):
            # init git in the repository's destination
            self.repository.init()
            self.service.connect()
            self.service.add(user=namespace, repo=repository)
            #
            if not default:
                if not alone and not name:
                    self.assert_added_remote_defaults()
                elif not alone and name:
                    self.assert_added_remote(name)
                    self.assert_added_remote('all')
                elif alone and not name:
                    self.assert_added_remote(self.service.name)
                elif alone and name:
                    self.assert_added_remote(name)
            else:
                if not alone and not name:
                    self.assert_added_remote_defaults()
                elif not alone and name:
                    self.assert_added_remote(name)
                    self.assert_added_remote('all')
                elif alone and not name:
                    self.assert_added_remote(self.service.name)
                elif alone and name:
                    self.assert_added_remote(name)
                self.assertTrue(
                    self.service.name in self.repository.branches[0].tracking_branch().name,
                    'Could not set "" as tracking branch master'.format(self.service.name)
                )

    def action_open(self, cassette_name, namespace, repository):
        #with self.recorder.use_cassette('_'.join(['test', self.service.name, cassette_name])):
        pass


