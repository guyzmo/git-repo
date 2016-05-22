#!/usr/bin/env python

from tempfile import TemporaryDirectory
from git import Repo, Git

from testfixtures import Replace, ShouldRaise, compare
from testfixtures.popen import MockPopen

import os
import logging
import betamax

from git_repo.repo import RepositoryService, main

class RepositoryMockup(RepositoryService):
    fqdn = 'http://example.org'
    def __init__(self, *args, **kwarg):
        super(RepositoryMockup, self).__init__(*args, **kwarg)
        self._did_pull = None
        self._did_clone = None
        self._did_add = None
        self._did_open = None
        self._did_connect = None
        self._did_delete = None
        self._did_create = None
        self._did_fork = None
        self._did_user = False
        self._did_gist_list = None
        self._did_gist_fetch = None
        self._did_gist_clone = None
        self._did_gist_create = None
        self._did_gist_delete = None
        self._did_request_list = None
        self._did_request_fetch = None

    def pull(self, *args, **kwarg):
        self._did_pull = (args, kwarg)

    def clone(self, *args, **kwarg):
        self._did_clone = (args, kwarg)

    def add(self, *args, **kwarg):
        self._did_add = (args, kwarg)

    def open(self, *args, **kwarg):
        self._did_open = (args, kwarg)

    def connect(self):
        self._did_connect = True

    def delete(self, *args, **kwarg):
        self._did_delete = (args, kwarg)

    def create(self, *args, **kwarg):
        self._did_create = (args, kwarg)

    def fork(self, *args, **kwarg):
        self._did_fork = (args, kwarg)

    def gist_list(self, *args, **kwarg):
        self._did_gist_list = (args, kwarg)
        if len(args) == 0:
            return [('id1', 'value1'),
                    ('id2', 'value2'),
                    ('id3', 'value3')]
        elif len(args) == 1:
            if args[0] == 'bad':
                raise Exception('bad gist!')
            else:
                return [('lang1', 'size1', 'name1'),
                        ('lang2', 'size2', 'name2'),
                        ('lang3', 'size3', 'name3')]

    def gist_fetch(self, *args, **kwarg):
        self._did_gist_fetch = (args, kwarg)
        if args[0] == 'bad':
            raise Exception('bad gist!')
        elif args[1] == 'bad':
            raise Exception('bad gist file!')
        else:
            return "content of a gist"

    def gist_clone(self, *args, **kwarg):
        self._did_gist_clone = (args, kwarg)
        if args[0] == 'bad':
            raise Exception('bad gist!')

    def gist_create(self, *args, **kwarg):
        self._did_gist_create = (args, kwarg)
        if 'exists' in args[0]:
            raise Exception('gist exists!')
        return 'https://gists/42'

    def gist_delete(self, *args, **kwarg):
        self._did_gist_delete = (args, kwarg)
        if args[0] == 'bad':
            raise Exception('bad gist!')

    def request_list(self, *args, **kwarg):
        self._did_request_list = (args, kwarg)
        return [('1', 'desc1', 'http://request/1'),
                ('2', 'desc2', 'http://request/2'),
                ('3', 'desc3', 'http://request/3')]

    def request_fetch(self, *args, **kwarg):
        self._did_request_fetch = (args, kwarg)
        if args[-1] == 'bad':
            raise Exception('bad request for merge!')
        return "pr/42"

    @property
    def user(self):
        self._did_user = True
        return 'foobar'

    def get_repository(self, *args, **kwarg):
        return {}

class GitRepoMainTestCase():
    def setup_method(self, method):
        self.log.info('GitRepoMainTestCase.setup_method({})'.format(method))
        self.tempdir = TemporaryDirectory()
        RepositoryService.service_map = {
            'github': RepositoryMockup,
            'gitlab': RepositoryMockup,
            'bitbucket': RepositoryMockup,
        }
        RepositoryService.command_map = {
            'hub': 'github',
            'lab': 'gitlab',
            'bb': 'bitbucket',
        }

    def teardown_method(self, method):
        self.log.info('GitRepoMainTestCase.teardown_method({})'.format(method))
        RepositoryService._current = RepositoryMockup(c={})
        self.tempdir.cleanup()

    def setup_args(self, d, args={}):
        cli_args = {
            '--force': False,
            '--help': False,
            '--path': '.',
            '--verbose': 4,
            '--no-clone': False,
            '--tracking': 'master',
            '--alone': False,
            '--add': False,
            '<name>': None,
            '<branch>': None,
            '<target>': self.target,
            '<user>/<repo>': '',
            'add': False,
            'clone': False,
            'create': False,
            'delete': False,
            'fork': False,
            'gist': False,
            'fetch': False,
            'fork': False,
            'list': False,
            'ls': False,
            'open': False,
            '--secret': False,
            '<description>': None,
            '<gist>': None,
            '<gist_file>': None,
            '<gist_path>': [],
            'request': False,
            '<request>': None,
            '<user>/<repo>': None,
        }
        cli_args.update(d)
        cli_args.update(args)
        return cli_args

    def main_add(self, repo, rc=0, args={}):
        os.mkdir(os.path.join(self.tempdir.name, repo.split('/')[-1]))
        Repo.init(os.path.join(self.tempdir.name, repo.split('/')[-1]))
        assert rc == main(self.setup_args({
            'add': True,
            '<user>/<repo>': repo,
            '--path': self.tempdir.name
        }, args)), "Non {} result for add".format(rc)
        return RepositoryService._current._did_add

    def main_clone(self, repo, rc=0, args={}):
        assert rc == main(self.setup_args({
            'clone': True,
            '<user>/<repo>': repo,
            '--path': self.tempdir.name
        }, args)), "Non {} result for clone".format(rc)
        return RepositoryService._current._did_clone

    def main_create(self, repo, rc=0, args={}):
        os.mkdir(os.path.join(self.tempdir.name, repo.split('/')[-1]))
        Repo.init(os.path.join(self.tempdir.name, repo.split('/')[-1]))
        assert rc == main(self.setup_args({
            'create': True,
            '<user>/<repo>': repo,
            '--path': self.tempdir.name
        }, args)), "Non {} result for create".format(rc)
        return RepositoryService._current._did_create

    def main_delete(self, repo, rc=0, args={}):
        os.mkdir(os.path.join(self.tempdir.name, repo.split('/')[-1]))
        Repo.init(os.path.join(self.tempdir.name, repo.split('/')[-1]))
        assert rc == main(self.setup_args({
            'delete': True,
            '<user>/<repo>': repo,
            '--path': self.tempdir.name,
        }, args)), "Non {} result for delete".format(rc)
        return RepositoryService._current._did_delete

    def main_fork(self, repo, rc=0, args={}):
        assert rc == main(self.setup_args({
            'fork': True,
            '<user>/<repo>': repo,
            '--clone': True,
            '--path': self.tempdir.name
        }, args)), "Non {} result for fork".format(rc)
        return RepositoryService._current._did_fork

    def main_gist_list(self, rc=0, args={}):
        assert rc == main(self.setup_args({
            'gist': True,
            'list': True,
        }, args)), "Non {} result for gist list".format(rc)
        return RepositoryService._current._did_gist_list

    def main_gist_ls(self, rc=0, args={}):
        assert rc == main(self.setup_args({
            'gist': True,
            'ls': True,
        }, args)), "Non {} result for gist ls".format(rc)
        return RepositoryService._current._did_gist_list

    def main_gist_clone(self, rc=0, args={}):
        assert rc == main(self.setup_args({
            'gist': True,
            'clone': True,
        }, args)), "Non {} result for gist clone".format(rc)
        return RepositoryService._current._did_gist_clone

    def main_gist_fetch(self, rc=0, args={}):
        assert rc == main(self.setup_args({
            'gist': True,
            'fetch': True,
        }, args)), "Non {} result for gist fetch".format(rc)
        return RepositoryService._current._did_gist_fetch

    def main_gist_create(self, rc=0, args={}):
        assert rc == main(self.setup_args({
            'gist': True,
            'create': True,
        }, args)), "Non {} result for gist create".format(rc)
        return RepositoryService._current._did_gist_create

    def main_gist_delete(self, rc=0, args={}):
        assert rc == main(self.setup_args({
            'gist': True,
            'delete': True,
        }, args)), "Non {} result for gist delete".format(rc)
        return RepositoryService._current._did_gist_delete

    def main_request_list(self, repo, rc=0, args={}):
        assert rc == main(self.setup_args({
            'request': True,
            'list': True,
            '<user>/<repo>': repo,
            '--clone': True,
            '--path': self.tempdir.name
        }, args)), "Non {} result for request list".format(rc)
        return RepositoryService._current._did_request_list

    def main_request_fetch(self, repo, rc=0, args={}):
        assert rc == main(self.setup_args({
            'request': True,
            'fetch': True,
            '<user>/<repo>': repo,
            '--clone': True,
            '--path': self.tempdir.name
        }, args)), "Non {} result for request fetch".format(rc)
        return RepositoryService._current._did_request_fetch

    def main_open(self, repo, rc=0, args={}):
        os.mkdir(os.path.join(self.tempdir.name, repo.split('/')[-1]))
        Repo.init(os.path.join(self.tempdir.name, repo.split('/')[-1]))
        assert rc == main(self.setup_args({
            'open': True,
            '<user>/<repo>': repo,
            '--path': self.tempdir.name
        }, args)), "Non {} result for open".format(rc)
        return RepositoryService._current._did_open

    def main_noop(self, repo, rc=1, args={}):
        assert rc == main(self.setup_args({
            '<user>/<repo>': repo,
            '--path': self.tempdir.name
        }, args)), "Non {} result for no-action".format(rc)

class GitRepoTestCase():
    def setup_method(self, method):
        self.log.info('GitRepoTestCase.setup_method({})'.format(method))
        # build temporary directory
        self.tempdir = TemporaryDirectory()
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
        self.get_requests_session().headers['Accept-Encoding'] = 'identity'
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

    def teardown_method(self, method):
        self.log.info('GitRepoTestCase.teardown_method({})'.format(method))
        self.tempdir.cleanup()

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
                ('git version', b'git version 2.8.0', b'', 0),
                ('git pull --progress -v {} master'.format(self.service.name), b'', '\n'.join([
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
                self.service.fork(remote_namespace, repository, clone=True)

    def action_fork__no_clone(self, cassette_name, local_namespace, remote_namespace, repository):
        # hijack subprocess call
        with self.mockup_git(local_namespace, repository):
            # prepare output for git commands
            remote_slug = self.service.format_path(namespace=remote_namespace, repository=repository, rw=True)
            local_slug = self.service.format_path(namespace=local_namespace, repository=repository, rw=True)
            self.set_mock_popen_commands([
                ('git remote add upstream {}'.format(remote_slug), b'', b'', 0),
                ('git remote add all {}'.format(local_slug), b'', b'', 0),
                ('git remote add {} {}'.format(self.service.name, local_slug), b'', b'', 0),
                ('git version', b'git version 2.8.0', b'', 0),
                ('git pull --progress -v {} master'.format(self.service.name), b'', '\n'.join([
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
                self.service.fork(remote_namespace, repository, clone=False)

    def action_clone(self, cassette_name, namespace, repository):
        # hijack subprocess call
        with self.mockup_git(namespace, repository):
            local_slug = self.service.format_path(namespace=namespace, repository=repository, rw=True)
            self.set_mock_popen_commands([
                ('git remote add all {}'.format(local_slug), b'', b'', 0),
                ('git remote add {} {}'.format(self.service.name, local_slug), b'', b'', 0),
                ('git version', b'git version 2.8.0', b'', 0),
                ('git pull --progress -v {} master'.format(self.service.name), b'', '\n'.join([
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
            self.service.create(namespace, repository, add=True)
            #
            self.assert_repository_exists(namespace, repository)
            self.assert_added_remote_defaults()

    def action_create__no_add(self, cassette_name, namespace, repository):
        with self.recorder.use_cassette('_'.join(['test', self.service.name, cassette_name])):
            self.service.connect()
            self.service.create(namespace, repository, add=False)
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

    def action_request_list(self, cassette_name, namespace, repository, rq_list_data=[]):
        with self.recorder.use_cassette('_'.join(['test', self.service.name, cassette_name])):
            self.service.connect()
            requests = list(self.service.request_list(user=namespace, repo=repository))
            for i, rq in enumerate(rq_list_data):
                assert requests[i] == rq

    def action_request_fetch(self, cassette_name, namespace, repository, request, pull=False):
        with self.recorder.use_cassette('_'.join(['test', self.service.name, cassette_name])):
            self.service.connect()
            self.service.clone(namespace, repository, rw=False)
            self.service.request_fetch(repository, namespace, request)
            assert self.repository.branches[-1].name == 'request/{}'.format(request)

    def action_gist_list(self, cassette_name, gist=None, gist_list_data=[]):
        with self.recorder.use_cassette('_'.join(['test', self.service.name, cassette_name])):
            self.service.connect()
            if gist is None:
                gists = list(self.service.gist_list())
                for i, g in enumerate(gist_list_data):
                    assert gists[i] == g
            else:
                gist_files = list(self.service.gist_list())
                for i, gf in enumerate(gist_list_data):
                    assert gist_files[i] == gf

    def action_gist_clone(self, cassette_name, gist):
        with self.mockup_git(None, None):
            self.set_mock_popen_commands([
                ('git version', b'git version 2.8.0', b'', 0),
                ('git remote add gist {}.git'.format(gist), b'', b'', 0),
                ('git pull --progress -v gist master', b'', b'\n'.join([
                    b'POST git-upload-pack (140 bytes)',
                    b'remote: Counting objects: 8318, done.',
                    b'remote: Compressing objects: 100% (3/3), done.',
                    b'remote: Total 8318 (delta 0), reused 0 (delta 0), pack-reused 8315',
                    b'Receiving objects: 100% (8318/8318), 3.59 MiB | 974.00 KiB/s, done.',
                    b'Resolving deltas: 100% (5126/5126), done.',
                    bytes('From {}'.format(gist), 'utf-8'),
                    b' * branch            master     -> FETCH_HEAD']),
                0),
            ])
            with self.recorder.use_cassette('_'.join(['test', self.service.name, cassette_name])):
                self.service.connect()
                self.service.gist_clone(gist)


    def action_gist_fetch(self, cassette_name, gist, gist_file=None):
        with self.recorder.use_cassette('_'.join(['test', self.service.name, cassette_name])):
            self.service.connect()
            content = self.service.gist_fetch(gist, gist_file)
            return content

    def action_gist_create(self, cassette_name, description, gist_files, secret):
        with self.recorder.use_cassette('_'.join(['test', self.service.name, cassette_name])):
            self.service.connect()
            content = self.service.gist_create(gist_files, description, secret)

    def action_gist_delete(self, cassette_name, gist):
        with self.recorder.use_cassette('_'.join(['test', self.service.name, cassette_name])):
            self.service.connect()
            content = self.service.gist_delete(gist)

    def action_open(self, cassette_name, namespace, repository):
        self.set_mock_popen_commands([
            ('xdg-open {}'.format(self.service.format_path(namespace=namespace, repository=repository)), b'', b'', 0),
            ('open {}'.format(self.service.format_path(namespace=namespace, repository=repository)), b'', b'', 0),
        ])
        with Replace('subprocess.Popen', self.Popen):
            self.service.open(user=namespace, repo=repository)


