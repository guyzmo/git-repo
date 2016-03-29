#!/usr/bin/env python

from tempfile import TemporaryDirectory
from unittest import TestCase
from git import Repo, Git

from testfixtures import Replace, ShouldRaise, compare
from testfixtures.popen import MockPopen

import os
import logging
import betamax


class GitRepoTestCase(TestCase):
    def setUp(self):
        self.log.info('GitRepoTestCase')
        # build temporary directory
        self.tempdir = TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        # repository mockup (in a temporary place)
        self.repository = Repo.init(self.tempdir.name)
        # setup git command mockup
        self.Popen = MockPopen()
        self.Popen.mock.Popen_instance.stdin = None
        self.Popen.mock.Popen_instance.wait = lambda *a, **k: self.Popen.wait()
        self.Popen.mock.Popen_instance.__enter__ = lambda self: self
        self.Popen.mock.Popen_instance.__exit__ = lambda self, *a, **k: None
        # when initiating service with no repository, the connection is not triggered
        self.service = self.get_service()
        self.service.repository = self.repository
        # setup http api mockup
        self.recorder = betamax.Betamax(self.get_requests_session())
        # have git commands logged
        Git.GIT_PYTHON_TRACE = True
        FORMAT = '> %(message)s'
        formatter = logging.Formatter(fmt=FORMAT)
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logging.getLogger('git.cmd').removeHandler(logging.NullHandler())
        logging.getLogger('git.cmd').addHandler(handler)
        logging.getLogger('git.cmd').propagate = True
        # have HTTP requests logged
        import http.client
        http.client.HTTPConnection.debuglevel = 1
        logging.getLogger('requests.packages.urllib3').setLevel(logging.DEBUG)
        logging.getLogger('requests.packages.urllib3').propagate = True

    '''popen helper'''

    def set_mock_popen_commands(self, cmd_list):
        for cmd, out, err, rc in cmd_list:
            self.Popen.set_command(cmd, out, err, returncode=rc)

    def mockup_git(self, namespace, repository):
        # disable refspec check
        from git import remote
        remote.Remote._assert_refspec = lambda self: None
        # write FETCH_HEAD ref
        with open(os.path.join(self.repository.git_dir, 'FETCH_HEAD'), 'w') as f:
            f.write("749656b8b3b282d11a4221bb84e48291ca23ecc6" \
                    "		branch 'master' of git@{}/{}/{}".format(self.service.fqdn, namespace, repository))
        return Replace('git.cmd.Popen', self.Popen)

    '''assertion helpers'''

    def assert_repository_exists(self, namespace, repository):
        try:
            self.service.get_repository(namespace, repository)
        except Exception as err:
            raise AssertionError("Repository {}/{} not found on {}: {}".format(namespace,
                                                                               repository,
                                                                               self.service.name,
                                                                               err)) from err

    def assert_repository_not_exists(self, namespace, repository):
        try:
            self.service.get_repository(namespace, repository)
        except Exception as err:
            return
        #raise AssertionError("Repository {}/{} exists on {}".format(namespace,
        #                                                                       repository,
        #                                                                       self.service.name,
        #                                                                ))

    def assert_added_remote(self, remote):
        try:
            self.repository.remote(remote)
        except ValueError as err:
            raise AssertionError("Remote {} not in repository".format(remote)) from err

    def assert_added_remote_defaults(self):
        self.assert_added_remote(self.service.name)
        self.assert_added_remote('all')

    def assert_tracking_remote(self, remote_name=None, branch_name='master'):
        if not remote_name:
            remote_name = self.service.name
        for branch in self.repository.branches:
            if branch == branch_name:
                assert remote_name in self.repository.branches[0].tracking_branch().name, \
                    'Could not set "{}" as tracking branch master'.format(self.service.name)

    '''test cases templates'''

    def action_fork(self, cassette_name, local_namespace, remote_namespace, repository):
        # hijack subprocess call
        with self.mockup_git(local_namespace, repository):
            # prepare output for git commands
            remote_slug = self.service.format_path(namespace=remote_namespace, repository=repository, rw=True)
            local_slug = self.service.format_path(namespace=local_namespace, repository=repository, rw=True)
            self.set_mock_popen_commands([
                ('git remote add upstream {}'.format(remote_slug), b'', b'', 0),
                ('git remote add all {}'.format(local_slug), b'', b'', 0),
                ('git remote add {} {}'.format(self.service.name, local_slug), b'', b'', 0),
                ('git pull -v {} master'.format(self.service.name), b'', '\n'.join([
                    'POST git-upload-pack (140 bytes)',
                    'remote: Counting objects: 8318, done.',
                    'remote: Compressing objects: 100% (3/3), done.',
                    'remote: Total 8318 (delta 0), reused 0 (delta 0), pack-reused 8315',
                    'Receiving objects: 100% (8318/8318), 3.59 MiB | 974.00 KiB/s, done.',
                    'Resolving deltas: 100% (5126/5126), done.',
                    'From {}:{}/{}'.format(self.service.fqdn, local_namespace, repository),
                    ' * branch            master     -> FETCH_HEAD',
                    ' * [new branch]      master     -> {}/master'.format(self.service.name)]).encode('utf-8'),
                0)
            ])
            with self.recorder.use_cassette('_'.join(['test', self.service.name, cassette_name])):
                self.service.connect()
                self.service.fork(remote_namespace, repository)

    def action_clone(self, cassette_name, namespace, repository):
        # hijack subprocess call
        with self.mockup_git(namespace, repository):
            local_slug = self.service.format_path(namespace=namespace, repository=repository, rw=True)
            self.set_mock_popen_commands([
                ('git remote add all {}'.format(local_slug), b'', b'', 0),
                ('git remote add {} {}'.format(self.service.name, local_slug), b'', b'', 0),
                ('git pull -v {} master'.format(self.service.name), b'', '\n'.join([
                    'POST git-upload-pack (140 bytes)',
                    'remote: Counting objects: 8318, done.',
                    'remote: Compressing objects: 100% (3/3), done.',
                    'remote: Total 8318 (delta 0), reused 0 (delta 0), pack-reused 8315',
                    'Receiving objects: 100% (8318/8318), 3.59 MiB | 974.00 KiB/s, done.',
                    'Resolving deltas: 100% (5126/5126), done.',
                    'From {}:{}/{}'.format(self.service.fqdn, namespace, repository),
                    ' * branch            master     -> FETCH_HEAD',
                    ' * [new branch]      master     -> {}/master'.format(self.service.name)]).encode('utf-8'),
                0)
            ])
            with self.recorder.use_cassette('_'.join(['test', self.service.name, cassette_name])):
                self.service.connect()
                self.service.clone(namespace, repository)

    def action_create(self, cassette_name, namespace, repository):
        with self.recorder.use_cassette('_'.join(['test', self.service.name, cassette_name])):
            self.service.connect()
            self.service.create(namespace, repository)
            #
            self.assert_repository_exists(namespace, repository)
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
                namespace = self.service.user
            self.assert_repository_not_exists(namespace, repository)

    def action_add(self, cassette_name, namespace, repository, alone=False, name=None, tracking='master'):
        with self.recorder.use_cassette('_'.join(['test', self.service.name, cassette_name])):
            # init git in the repository's destination
            self.repository.init()
            self.service.connect()
            self.service.add(user=namespace, repo=repository, alone=alone, name=name, tracking=tracking)
            #
            if not tracking:
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
                    self.assert_tracking_remote()
                elif not alone and name:
                    self.assert_added_remote(name)
                    self.assert_added_remote('all')
                    self.assert_tracking_remote(name)
                elif alone and not name:
                    self.assert_added_remote(self.service.name)
                    self.assert_tracking_remote(branch_name=tracking)
                elif alone and name:
                    self.assert_added_remote(name)
                    self.assert_tracking_remote(name, tracking)

    def action_open(self, cassette_name, namespace, repository):
        self.set_mock_popen_commands([
            ('xdg-open {}'.format(self.service.format_path(namespace=namespace, repository=repository)), b'', b'', 0),
            ('open {}'.format(self.service.format_path(namespace=namespace, repository=repository)), b'', b'', 0),
        ])
        with Replace('subprocess.Popen', self.Popen):
            self.service.open(user=namespace, repo=repository)


