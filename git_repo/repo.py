#!/usr/bin/env python

'''
Usage:
    {self} [-p|-v|-h] <target> add <user>/<repo>
    {self} [-p|-v|-h] <target> clone <user>/<repo> [<branch>]
    {self} [-p|-v|-h] <target> create <user>/<repo>
    {self} [-p|-v|-h] <target> open [<user>/<repo>]

Commands:
    add                 Add the service as a remote on this repository
    clone               Clones this repository from the service
    create              Make this repository a new remote on the service
    open                Open the given or current repository in a browser

Arguments:
    <user>/<repo>       Repository to work with
    <branch>            Branch to pull (when cloning) [default: master]
    -p,--path=<path>    Path to work on [default: .]
    -v,--verbose        Makes it more chatty
    -h,--help           Shows this message

Configuration options:
    alias               Name to use for the git remote
    url                 URL of the repository
    private-key         Private key to use for connecting to the service
    type                Name of the service to use (github, gitlab, bitbucket)

Configuration example:

[gitrepo "gitlab"]
    private-key = YourSecretKey
    alias = lab

[gitrepo "personal"]
    type = gitlab
    private-key = YourSecretKey
    url = http://custom.org

{self} version {version}, Copyright ⓒ2016 Bernard `Guyzmo` Pratz
{self} comes with ABSOLUTELY NO WARRANTY; for more informations
read the LICENSE file available in the sources, or check
out: http://www.gnu.org/licenses/gpl-2.0.txt
'''

import sys
import pkg_resources

__version__ = pkg_resources.require('git-repo')[0].version
__author__ = 'Bernard `Guyzmo` Pratz <guyzmo+git_repo@m0g.net>'
__contributors__ = []

from subprocess import call
from docopt import docopt
from git import Repo

import json


####################################################################################
# repository_service.py

if 'mac' in sys.platform:
    OPEN_COMMAND = 'open'
else:
    OPEN_COMMAND = 'xdg-open'


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
    service_map = dict()
    command_map = dict()

    @classmethod
    def get_service(cls, repository, command):
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
        self.repository = r
        self.config = c

        name = ' '.join(c['__name__'].replace('"', '').split(' ')[1:])
        if name != self.name:
            if 'url' not in c:
                raise ValueError('Custom services SHALL have an URL setting.')
            self.url = c['url']
            self.name = name
        self._privatekey = c.get('privatekey', None)
        self._alias = c.get('alias', self.name)
        self._url = c.get('url', self.url)

    def clone(self, user, repo_name, branch='master'):
        print('git clone {}/{}/{} {}'.format(self.url, user, repo_name, branch))
        self.repository.create_remote(self.name, '{}/{}/{}'.format(self.url, user, repo_name))
        # TODO add option for making this remote default for the branch
        self.repository.remotes[0].pull(branch, kwargs={'-u': 'master'})

    def add(self, repo, default=False):
        '''Adding repository as remote'''
        # removing remote if it already exists
        for r in self.repository.remotes:
            if r.name == self.name:
                self.repository.delete_remote(r)
                break
        # adding it back
        if default:
            self.repository.create_remote(self.name, '{}/{}'.format(self.url, repo, kwargs={'-m': 'master'}))  # TODO does not work
        else:
            self.repository.create_remote(self.name, '{}/{}'.format(self.url, repo))

    def open(self, repo=None):
        if not repo:
            url = self.c.get('remote "origin"', 'url')
            call([OPEN_COMMAND, url])
        else:
            call([OPEN_COMMAND, '{}/{}'.format(self.url, repo)])

    def create(self, repo):
        raise NotImplementedError

####################################################################################
# repository_bitbucket.py


@register_target('bb', 'bitbucket')
class BitbucketService(RepositoryService):
    url = 'https://bitbucket.org'

    def create(self, repo):
        from bitbucket.bitbucket import Bitbucket
        username, password = self._privatekey.split(':')
        repo_name = repo
        if '/' in repo:
            user, repo_name = repo.split('/')
        print("creating bloody repo on bitbucket: ", self.url, ':', user, repo_name)
        bb = Bitbucket(username, password)
        try:
            bb.repository.create(repo_name, scm='git')
        except Exception as err:
            print(err)
            print(dir(err))
            if err.message == 'name already exists on this account':
                raise Exception("Project already exists.")
            else:
                raise Exception("Unhandled error.")
        self.add(repo, default=True)

####################################################################################
# repository_github.py


@register_target('hub', 'github')
class GithubService(RepositoryService):
    url = 'https://github.com'

    def create(self, repo):
        repo_name = repo
        if '/' in repo:
            user, repo_name = repo.split('/')
        print("creating bloody repo on github: ", self.url, ':', user, repo_name)
        import github3
        gh = github3.login(token=self._privatekey)
        try:
            gh.create_repo(repo_name)
        except github3.models.GitHubError as err:
            print(err.message)
            if err.message == 'name already exists on this account':
                raise Exception("Project already exists.")
            else:
                raise Exception("Unhandled error.")
        self.add(repo, default=True)


####################################################################################
# repository_gitlab.py


@register_target('lab', 'gitlab')
class GitlabService(RepositoryService):
    url = 'https://gitlab.com'

    def create(self, repo):
        repo_name = repo
        if '/' in repo:
            user, repo_name = repo.split('/')
        print("creating bloody repo on gitlab: ", repo, '→', self.url, ':', user, repo_name)
        from gitlab import Gitlab
        from gitlab.exceptions import GitlabCreateError
        print(self._privatekey)
        try:
            Gitlab(self.url, self._privatekey).projects.create(data={
                'name': repo_name,
                # 'namespace_id': user, # TODO does not work
            })
        except GitlabCreateError as err:
            if json.loads(err.response_body.decode('utf-8'))['message']['name'][0] == 'has already been taken':
                raise Exception("Project already exists.")
            else:
                raise Exception("Unhandled error.")
        self.add(repo, default=True)


####################################################################################


def main(args):
    print(args)

    if args['create'] or args['add']:
        repository = Repo()
        service = RepositoryService.get_service(repository, args['<target>'])

        if args['create']:
            print('check that "." is a git repository')
            print('execute: API', service.name, 'CREATE', args['<user>/<repo>'])
            print('execute: git remote add', service.name, service.url, args['<user>/<repo>'])
            service.create(args['<user>/<repo>'])
            print('Success creating remote repository `{}/{}`, with local remote `{}`'.format(
                service.url, args['<user>/<repo>'],
                service.name))
        elif args['add']:
            service.add(args['<user>/<repo>'])
            print('Success adding `{}` as remote named `{}`'.format(args['<user>/<repo>'], service.name))
        return 0

    elif args['clone']:
        user, repo_name = args['<user>/<repo>'].split('/')
        repository = Repo.init(repo_name)
        service = RepositoryService.get_service(repository, args['<target>'])
        if args['<branch>']:
            service.clone(user, repo_name, args['<branch>'])
        else:
            service.clone(user, repo_name)
        print('Success cloning `{}/{}` into `{}`!'.format(service.url,
                                                          args['<user>/<repo>'],
                                                          repo_name))
        return 0

    elif args['open']:
        try:
            repository = Repo()
        except:
            repository = None
        RepositoryService.get_service(repository, args['<target>']).open(args['<user>/<repo>'])
        return 0

    print('Unknown action.')
    print('Please consult help page (--help).')
    return 1


def cli():
    main(docopt(__doc__.format(self=sys.argv[0], version=__version__)))

if __name__ == '__main__':
    cli()
