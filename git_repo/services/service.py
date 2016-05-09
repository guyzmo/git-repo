#!/usr/bin/env python

import logging
log = logging.getLogger('git_repo.base')

import os
import sys

from git import RemoteProgress
from progress.bar import IncrementalBar as Bar

from ..exceptions import ArgumentError

'''select open command'''

from subprocess import call

if 'mac' in sys.platform: #pragma: no cover
    OPEN_COMMAND = 'open'
else: #pragma: no cover
    OPEN_COMMAND = 'xdg-open'

'''monkey patching of git module'''

# Monkey patching of missing command Remote.set_url
# TODO make a PR on pythongit
def set_url(self, url, **kwargs): # pragma: no cover
    scmd = 'set-url'
    kwargs['insert_kwargs_after'] = scmd
    self.repo.git.remote(scmd, self.name, url, **kwargs)
    return self

def list_urls(self): # pragma: no cover
    '''Return the list of all configured URL targets'''
    remote_details = self.repo.git.remote("show", self.name)
    for line in remote_details.split('\n'):
        if '  Push  URL:' in line:
            yield line.split(': ')[-1]


import git
git.remote.Remote.set_url = set_url
git.remote.Remote.list = property(list_urls)


class ProgressBar(RemoteProgress): # pragma: no cover
    '''Nice looking progress bar for long running commands'''
    def setup(self, repo_name):
        self.bar = Bar(message='Pulling from {}'.format(repo_name), suffix='')

    def update(self, op_code, cur_count, max_count=100, message=''):
        #log.info("{}, {}, {}, {}".format(op_code, cur_count, max_count, message))
        max_count = int(max_count or 100)
        if max_count != self.bar.max:
            self.bar.max = max_count
        self.bar.goto(int(cur_count))


def register_target(repo_cmd, repo_service):
    """Decorator to register a class with an repo_service"""
    def decorate(klass):
        log.debug('Loading service module class: {}'.format(klass.__name__) )
        klass.command = repo_cmd
        klass.name = repo_service
        RepositoryService.service_map[repo_service] = klass
        RepositoryService.command_map[repo_cmd] = repo_service
        return klass
    return decorate


class RepositoryService:
    '''Base class for all repository services'''
    service_map = dict()
    command_map = dict()

    # this symbol is made available for testing purposes
    _current = None

    @classmethod
    def get_service(cls, repository, command):
        '''Accessor for a repository given a command

        :param repository: git-python repository instance
        :param command: aliased name of the service
        :return: instance for using the service
        '''
        if not repository:
            config = git.config.GitConfigParser(os.path.join(os.environ['HOME'], '.gitconfig'))
        else:
            config = repository.config_reader()
        target = cls.command_map.get(command, command)
        conf_section = list(filter(lambda n: 'gitrepo' in n and target in n, config.sections()))

        # check configuration constraints
        if len(conf_section) == 0:
            if not target:
                raise ValueError('Service {} unknown'.format(target))
            else:
                config = dict()
        elif len(conf_section) > 1:
            raise ValueError('Too many configurations for service {}'.format(target))
        # get configuration section as a dict
        else:
            config = config._sections[conf_section[0]]

        if target in cls.service_map:
            service = cls.service_map.get(target, cls)
            service.name = target
        else:
            if 'type' not in config:
                raise ValueError('Missing service type for custom service.')
            if config['type'] not in cls.service_map:
                raise ValueError('Service type {} does not exists.')
            service = cls.service_map.get(config['type'], cls)

        cls._current = service(repository, config)
        return cls._current

    def __init__(self, r=None, c=None):
        '''
        :param r: git-python repository instance
        :param c: configuration data

        Build a repository service instance, store configuration and parameters
        And launch the connection to the service
        '''

        self.repository = r
        self.config = c

        # if there's a configuration file, update the names accordingly
        if c:
            name = ' '.join(c['__name__'].replace('"', '').split(' ')[1:])
            if name != self.name:
                if 'fqdn' not in c:
                    raise ValueError('Custom services SHALL have an URL setting.')
                self.fqdn = c['fqdn']
                self.name = name
        # if not in the configuration file, retrieve the private key from the
        # environment (useful for travis configuration), otherwise, make it None.
        # using "token" > "private_token" > "privatekey" in configuration file to avoid
        # confusion with the SSH keys (yes that happened).
        # NB: `git config` doesn't parse underscores in option names, token.
        self._privatekey = os.environ.get('PRIVATE_KEY_{}'.format(self.name.upper()),
                                          c.get('token',
                                                c.get('private_token',
                                                      c.get('privatekey', None))))
        self._alias = c.get('alias', self.name)
        self.fqdn = c.get('fqdn', self.fqdn)

        # if service has a repository configured, connect
        if r:
            self.connect()

    '''URL handling'''

    '''name of the git user to use for SSH remotes'''
    git_user = 'git'

    @property
    def url_ro(self):
        '''Property that returns the HTTP URL of the service'''
        return 'https://{}'.format(self.fqdn)

    @property
    def url_rw(self):
        return '{}@{}'.format(self.git_user, self.fqdn)

    def format_path(self, repository, namespace=None, rw=False):
        '''format the repository's URL

        :param repository: name of the repository
        :param namespace: namespace of the repository
        :param rw: return a git+ssh URL if true, an https URL otherwise
        :return: the full URI of the repository ready to use as remote

        if namespace is not given, repository is expected to be of format
        `<namespace>/<repository>`.
        '''
        repo = repository
        if namespace:
            repo = '{}/{}'.format(namespace, repository)

        if not rw and '/' in repo:
            return '{}/{}'.format(self.url_ro, repo)
        elif rw and '/' in repo:
            return '{}:{}'.format(self.url_rw, repo)
        else:
            raise ArgumentError("Cannot tell how to handle this url: `{}/{}`!".format(user, repo_name))

    def pull(self, remote, branch=None):
        '''Pull a repository
        :param remote: git-remote instance
        :param branch: name of the branch to pull
        '''
        pb = ProgressBar()
        pb.setup(self.name)
        if branch:
            remote.pull(branch, progress=pb)
        else: # pragma: no cover
            remote.pull(progress=pb)
        print()

    def fetch(self, remote, remote_branch, local_branch):
        '''Pull a repository
        :param remote: git-remote instance
        :param branch: name of the branch to pull
        '''
        pb = ProgressBar()
        pb.setup(self.name)
        remote.fetch(':'.join([remote_branch, local_branch]), progress=pb)
        print()

    def clone(self, user, repo, branch='master', rw=True):
        '''Clones a new repository

        :param user: namespace of the repository
        :param repo: name slug of the repository
        :Param branch: branch to pull as tracking

        This command is fairly simple, and pretty close to the real `git clone`
        command, except it does not take a full path, but just a namespace/slug
        path for a given service.
        '''
        log.info('Cloning {}…'.format(repo))

        remote = self.add(user=user, repo=repo, tracking=True, rw=rw)
        self.pull(remote, branch)

    def add(self, repo, user=None, name=None, tracking=False, alone=False, rw=True):
        '''Adding repository as remote

        :param repo: Name slug of the repository to add
        :param name: Name of the remote when stored
        :param tracking: When set, makes this remote the tracking for master operations
        :param alone: When set, exclude this remote from the "all" remote

        This method creates a new remote within the current repository *repo*.
        It chooses the name of the repository based on the service's name as
        held by current instance of RepositoryService, or uses the *name*
        parameter.

        It also creates an *all* remote that contains all the remotes added by
        this tool, to make it possible to push to all remotes at once.
        '''
        name = name or self.name

        if not user:
            if '/' in repo:
                user, repo = repo.split('/')
            else:
                raise ArgumentError('Unable to parse repository {}, missing path separator.'.format(repo))

        # removing remote if it already exists
        # and extract all repository
        all_remote = None
        for r in self.repository.remotes:
            if r.name == name:
                self.repository.delete_remote(r)
            # find and stash the remote 'all'
            elif r.name == 'all':
                all_remote = r
        # update remote 'all'
        if not alone:
            # if remote all does not exists
            if not all_remote:
                self.repository.create_remote('all', self.format_path(repo, user, rw=rw))
            else:
                url = self.format_path(repo, user, rw=True)
                # check if url not already in remote all
                if url not in all_remote.list:
                    all_remote.set_url(url=self.format_path(repo, user, rw=rw), add=True)

        # adding "self" as the tracking remote
        if tracking:
            remote = self.repository.create_remote(name, self.format_path(repo, user, rw=rw))
            # lookup tracking branch (usually master)
            for branch in self.repository.branches:
                if tracking == branch.name:
                    # set that branch as tracking
                    branch.set_tracking_branch(remote.refs[0])
                    break
            return remote
        else:
            return self.repository.create_remote(name, self.format_path(repo, user, rw=rw))

    def open(self, user=None, repo=None):
        '''Open the URL of a repository in the user's browser'''
        call([OPEN_COMMAND, self.format_path(repo, namespace=user, rw=False)])

    def connect(self): #pragma: no cover
        '''Brings up the connection to the remote service's API

        Meant to be overloaded by subclass
        '''
        raise NotImplementedError

    def delete(self, repo, user=None): #pragma: no cover
        '''Delete a remote repository on the service

        :param repo: name of the remote repository to delete

        Meant to be implemented by subclasses
        '''
        raise NotImplementedError

    def create(self, user, repo, add=False): #pragma: no cover
        '''Create a new remote repository on the service

        :param repo: name of the repository to create

        Meant to be implemented by subclasses
        '''
        raise NotImplementedError

    def fork(self, user, repo, clone=False): #pragma: no cover
        '''Forks a new remote repository on the service
        and pulls commits from it

        :param repo: name of the repository to create

        Meant to be implemented by subclasses
        '''
        raise NotImplementedError

    def gist_list(self):
        '''Lists gists

        Meant to be implemented by subclasses
        '''
        raise NotImplementedError

    def gist_fetch(self, gist): #pragma: no cover
        '''Fetches a published gist

        Meant to be implemented by subclasses
        '''
        raise NotImplementedError

    def gist_clone(self, gist): #pragma: no cover
        '''Clones a gist

        Meant to be implemented by subclasses
        '''
        raise NotImplementedError

    def gist_create(self, gist_path, secret=False): #pragma: no cover
        '''Pushes a new gist

        Meant to be implemented by subclasses
        '''
        raise NotImplementedError

    def gist_delete(self, gist_path, secret=False): #pragma: no cover
        '''Deletes a new gist

        Meant to be implemented by subclasses
        '''
        raise NotImplementedError

    def request_list(self, user, repo): #pragma: no cover
        '''Lists all available request for merging code
        sent to the remote repository

        :param repo: name of the repository to create

        Meant to be implemented by subclasses
        '''
        raise NotImplementedError

    def request_fetch(self, user, repo, request, pull=False): #pragma: no cover
        '''Fetches given request as a branch, and switch if pull is true

        :param repo: name of the repository to create

        Meant to be implemented by subclasses
        '''
        raise NotImplementedError

    @property
    def user(self): #pragma: no cover
        raise NotImplementedError


'''
register all services by importing their modules, from the ext pagckage

they are registered using the `register_target()` decorator, and added
to the `RepositorService.service_map` dictionary, and is accessed by the
`main()` function using the `RepositoryService.get_service()` method.
'''

from .ext import *

