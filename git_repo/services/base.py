#!/usr/bin/env python

import logging
log = logging.getLogger('git_repo.base')

import sys

from git import RemoteProgress
from progress.bar import IncrementalBar as Bar


'''select open command'''

if 'mac' in sys.platform:
    OPEN_COMMAND = 'open'
else:
    OPEN_COMMAND = 'xdg-open'

'''monkey patching of git module'''

# Monkey patching of missing command Remote.set_url
# TODO make a PR on pythongit
def set_url(self, url, **kwargs):
    scmd = 'set-url'
    kwargs['insert_kwargs_after'] = scmd
    self.repo.git.remote(scmd, self.name, url, **kwargs)
    return self

import git
git.remote.Remote.set_url = set_url


class ProgressBar(RemoteProgress):
    '''Nice looking progress bar for long running commands'''
    def setup(self, repo_name):
        # self.bar = Bar(message='Pulling from {}'.format(repo_name), suffix='')
        pass

    def update(self, op_code, cur_count, max_count=100, message=''):
        log.info("{}, {}, {}, {}".formatn(op_code, cur_count, max_count, message))
        # max_count = int(max_count or 100)
        # if max_count != self.bar.max:
        #     self.bar.max = max_count
        # self.bar.goto(int(cur_count))


def register_target(repo_cmd, repo_service):
    """Decorator to register a class with an repo_service"""
    def decorate(klass):
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

    @classmethod
    def get_service(cls, repository, command):
        '''Accessor for a repository given a command

        :param repository: git-python repository instance
        :param command: aliased name of the service
        :return: instance for using the service
        '''
        config = repository.config_reader()
        target = cls.command_map.get(command, command)
        conf_section = list(filter(lambda n: 'gitrepo' in n and target in n, config.sections()))

        # check configuration constraints
        if len(conf_section) == 0:
            raise ValueError('Service {} unknown'.format(target))
        elif len(conf_section) > 1:
            raise ValueError('Too many configurations for service {}'.format(target))
        # get configuration section as a dict
        config = config._sections[conf_section[0]]

        if target in cls.service_map:
            service = cls.service_map.get(target, cls)
        else:
            if 'type' not in config:
                raise ValueError('Missing service type for custom service.')
            if config['type'] not in cls.service_map:
                raise ValueError('Service type {} does not exists.')
            service = cls.service_map.get(config['type'], cls)

        return service(repository, config)

    def __init__(self, r, c):
        '''
        :param r: git-python repository instance
        :param c: configuration data

        Build a repository service instance, store configuration and parameters
        And launch the connection to the service
        '''
        self.repository = r
        self.config = c

        name = ' '.join(c['__name__'].replace('"', '').split(' ')[1:])
        if name != self.name:
            if 'fqdn' not in c:
                raise ValueError('Custom services SHALL have an URL setting.')
            self.fqdn = c['fqdn']
            self.name = name
        self._privatekey = c.get('privatekey', None)
        self._alias = c.get('alias', self.name)
        self.fqdn = c.get('fqdn', self.fqdn)

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

    def format_path(self, repo_name, user=None, rw=False):
        '''format the repository's URL

        :param repo_name: name of the repository
        :param user: namespace of the repository
        :param rw: return a git+ssh URL if true, an https URL otherwise
        :return: the full URI of the repository ready to use as remote

        if user is not given, repo_name is expected to be of format
        `<namespace>/<repository>`.
        '''
        repo = repo_name
        if user:
            repo = '{}/{}'.format(user, repo_name)

        if not rw and '/' in repo:
            return '{}/{}'.format(self.url_ro, repo)
        elif rw and '/' in repo:
            return '{}:{}'.format(self.url_rw, repo)
        else:
            raise Exception("Cannot tell how to handle this url: `{}/{}`!".format(user, repo_name))

    def pull(self, remote, branch=None):
        '''Pull a repository
        :param remote: git-remote instance
        :param branch: name of the branch to pull
        '''
        if branch:
            remote.pull(branch)#, progress=ProgressBar())
        else:
            remote.pull() #progress=ProgressBar())

    def clone(self, user, repo_name, branch='master'):
        '''Clones a new repository

        :param user: namespace of the repository
        :param repo_name: name slug of the repository
        :Param branch: default branch to pull

        This command is fairly simple, and pretty close to the real `git clone`
        command, except it does not take a full path, but just a namespace/slug
        path for a given service.
        '''
        log.info('Cloning {}…'.format(repo_name))

        remote = self.add(user=user, repo=repo_name, default=True)
        self.pull(remote, branch)

    def add(self, repo, user=None, name=None, default=False, alone=False):
        '''Adding repository as remote

        :param repo: Name slug of the repository to add
        :param name: Name of the remote when stored
        :param default: When set, makes this remote the default for master operations
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
                raise Exception('Unable to parse repository {}, missing path separator.'.format(repo))

        # removing remote if it already exists
        # and extract all repository
        all_remote = None
        for r in self.repository.remotes:
            if r.name == name:
                self.repository.delete_remote(r)
            elif r.name == 'all':
                all_remote = r
        # update remote 'all'
        if not alone:
            if not all_remote:
                # XXX remove current remote's url from all if already there to avoid doubles
                # pythongit API lacks ability to get URLs from a remote…
                self.repository.create_remote('all', self.format_path(repo, user, rw=True))
            else:
                all_remote.set_url(url=self.format_path(repo, user, rw=True), add=True)

        # adding "self" as the default remote
        if default:
            return self.repository.create_remote(name, self.format_path(repo, user, rw=True), master='master')
        else:
            return self.repository.create_remote(name, self.format_path(repo, user, rw=True))

    def delete(self, repo):
        '''Delete a remote repository on the service

        :param repo: name of the remote repository to delete

        Meant to be implemented by subclasses
        '''
        raise NotImplementedError

    def open(self, repo=None):
        '''Open the URL of a repository in the user's browser'''
        if not repo:
            url = self.c.get('remote "origin"', 'url')
            call([OPEN_COMMAND, url])
        else:
            call([OPEN_COMMAND, self.format_path(repo, rw=False)])

    def create(self, repo):
        '''Create a new remote repository on the service

        :param repo: name of the repository to create

        Meant to be implemented by subclasses
        '''
        raise NotImplementedError

    def fork(self, repo):
        '''Forks a new remote repository on the service
        and pulls commits from it

        :param repo: name of the repository to create

        Meant to be implemented by subclasses
        '''
        raise NotImplementedError


# register all services by importing their modules
from . import *


