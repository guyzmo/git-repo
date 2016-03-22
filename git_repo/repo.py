#!/usr/bin/env python

'''
Usage:
    {self} [--path=<path>] [-v -v...] <target> add <user>/<repo>
    {self} [--path=<path>] [-v -v...] <target> fork <user>/<repo> [<branch>]
    {self} [--path=<path>] [-v -v...] <target> clone <user>/<repo> [<branch>]
    {self} [--path=<path>] [-v -v...] <target> create <user>/<repo>
    {self} [--path=<path>] [-v -v...] <target> delete <user>/<repo> [-f]
    {self} [--path=<path>] [-v -v...] <target> open [<user>/<repo>]
    {self} --help

Tool for managing remote repository services.

Commands:
    add                 Add the service as a remote on this repository
    clone               Clones this repository from the service
    Fork                Fork (and clone) the repository from the service
    create              Make this repository a new remote on the service
    delete              Delete the remote repository
    open                Open the given or current repository in a browser

Options:
    <user>/<repo>       Repository to work with
    <branch>            Branch to pull (when cloning) [default: master]
    -p,--path=<path>    Path to work on [default: .]
    -f,--force          Do not ask for confirmation
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

from docopt import docopt
from subprocess import call
from git import Repo, RemoteProgress
from progress.bar import IncrementalBar as Bar

import os
import sys
import json
import logging
import pkg_resources

__version__ = pkg_resources.require('git-repo')[0].version
__author__ = 'Bernard `Guyzmo` Pratz <guyzmo+git_repo@m0g.net>'
__contributors__ = []

log = logging.getLogger('git_repo.repo')

####################################################################################
# repository_service.py

if 'mac' in sys.platform:
    OPEN_COMMAND = 'open'
else:
    OPEN_COMMAND = 'xdg-open'


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
        raise NotImplementedError

    def open(self, repo=None):
        if not repo:
            url = self.c.get('remote "origin"', 'url')
            call([OPEN_COMMAND, url])
        else:
            call([OPEN_COMMAND, self.format_path(repo, rw=False)])

    def create(self, repo):
        raise NotImplementedError

    def fork(self, repo):
        raise NotImplementedError

####################################################################################
# repository_bitbucket.py

from bitbucket.bitbucket import Bitbucket


@register_target('bb', 'bitbucket')
class BitbucketService(RepositoryService):
    fqdn = 'bitbucket.org'

    def monkey_patch(self):
        import types
        # XXX odious monkey patching, need to do a PR upstream on bitbucket-api
        # def get(self, user=None, repo_slug=None):
        #     """ Get a single repository on Bitbucket and return it."""
        #     username = user or self.bitbucket.username
        #     repo_slug = repo_slug or self.bitbucket.repo_slug or ''
        #     url = self.bitbucket.url('GET_REPO', username=username, repo_slug=repo_slug)
        #     return self.bitbucket.dispatch('GET', url, auth=self.bitbucket.auth)
        #
        # self.bb.repository.bitbucket.URLS['GET_REPO'] = 'repositories/%(username)s/%(repo_slug)s/'
        # self.bb.repository.get_repo = types.MethodType(get, self.bb.repository)

        def delete(self, user, repo_slug):
            url = self.bitbucket.url('DELETE_REPO', accountname=user, repo_slug=repo_slug)
            return self.bitbucket.dispatch('DELETE', url, auth=self.bitbucket.auth)

        self.bb.repository.bitbucket.URLS['DELETE_REPO'] = 'repositories/%(accountname)s/%(repo_slug)s'
        self.bb.repository.delete = types.MethodType(delete, self.bb.repository)

        def fork(self, user, repo_slug, new_name=None):
            url = self.bitbucket.url('FORK_REPO', username=user, repo_slug=repo_slug)
            new_repo = new_name or repo_slug
            return self.bitbucket.dispatch('POST', url, name=new_repo, auth=self.bitbucket.auth)

        self.bb.repository.bitbucket.URLS['FORK_REPO'] = 'repositories/%(username)s/%(repo_slug)s/fork'
        self.bb.repository.fork = types.MethodType(fork, self.bb.repository)

        from requests import Request, Session
        def dispatch(self, method, url, auth=None, params=None, **kwargs):
            """ Send HTTP request, with given method,
                credentials and data to the given URL,
                and return the success and the result on success.
            """
            r = Request(
                method=method,
                url=url,
                auth=auth,
                params=params,
                data=kwargs)
            s = Session()
            resp = s.send(r.prepare())
            status = resp.status_code
            text = resp.text
            error = resp.reason
            if status >= 200 and status < 300:
                if text:
                    try:
                        return (True, json.loads(text))
                    except TypeError:
                        pass
                    except ValueError:
                        pass
                return (True, text)
            elif status >= 300 and status < 400:
                return (
                    False,
                    'Unauthorized access, '
                    'please check your credentials.')
            elif status == 404:
                return (False, dict(message='Service not found', reason=error, code=status))
            elif status == 400:
                return (False, dict(message='Bad request sent to server.', reason=error, code=status))
            elif status == 401:
                return (False, dict(message='Not enough privileges.', reason=error, code=status))
            elif status == 403:
                return (False, dict(message='Not authorized.', reason=error, code=status))
            elif status == 402 or status >= 405:
                return (False, dict(message='Request error.', reason=error, code=status))
            elif status >= 500 and status < 600:
                    return (False, dict(message='Server error.', reason=error, code=status))
            else:
                return (False, dict(message='Unidentified error.', reason=error, code=status))

        self.bb.repository.bitbucket.dispatch = types.MethodType(dispatch, self.bb.repository.bitbucket)

    def connect(self):
        username, password = self._privatekey.split(':')
        self.bb = Bitbucket(username, password)
        self.monkey_patch()

    def create(self, repo):
        repo_name = repo
        if '/' in repo:
            user, repo_name = repo.split('/')
        try:
            self.bb.repository.create(repo_name, scm='git')
        except Exception as err:
            if err.message == 'name already exists on this account':
                raise Exception("Project already exists.")
            else:
                raise Exception("Unhandled error.")
        self.add(user=user, repo=repo_name, default=True)

    def fork(self, user, repo, branch='master'):
        log.info("Forking repository {}/{}…".format(user, repo))
        success, result = self.bb.repository.fork(user, repo)
        if not success:
            raise Exception("Couldn't complete fork: {message} (error #{code}: {reason})".format(**result))
        fork = result
        self.add(repo=repo, user=user, name='upstream', alone=True)
        remote = self.add(repo=fork['slug'], user=fork['owner'], default=True)
        self.pull(remote, branch)
        log.info("New forked repository available at {}".format(self.format_path(fork['slug'], fork['owner'])))

    def delete(self, repo, user=None):
        if not user:
            user = self.bb.user().name
        success, result = self.bb.repository.delete(user, repo)
        if not success and result['code'] == 404:
            raise Exception("Cannot delete: repository {}/{} does not exists.".format(user, repo))
        elif not success:
            raise Exception("Couldn't complete deletion: {message} (error #{code}: {reason})".format(**result))



####################################################################################
# repository_github.py

import github3

@register_target('hub', 'github')
class GithubService(RepositoryService):
    fqdn = 'github.com'

    def connect(self):
        self.gh = github3.login(token=self._privatekey)

    def create(self, repo):
        repo_name = repo
        if '/' in repo:
            user, repo_name = repo.split('/')
        try:
            self.gh.create_repo(repo_name)
        except github3.models.GitHubError as err:
            if err.message == 'name already exists on this account':
                raise Exception("Project already exists.")
            else:
                raise Exception("Unhandled error.")
        self.add(user=user, repo=repo_name, default=True)

    def fork(self, user, repo, branch='master'):
        log.info("Forking repository {}/{}…".format(user, repo))
        try:
            fork = self.gh.repository(user, repo).create_fork()
        except github3.models.GitHubError as err:
            if err.message == 'name already exists on this account':
                raise Exception("Project already exists.")
            else:
                raise Exception("Unhandled error: {}".format(err))
        self.add(user=user, repo=repo, name='upstream', alone=True)
        remote = self.add(repo=fork.full_name, user=self.gh.user().name, default=True)
        self.pull(remote, branch)
        log.info("New forked repository available at {}/{}".format(self.url_ro,
                                                                   fork.full_name))

    def delete(self, repo_name, user=None):
        if not user:
            user = self.gh.user().name
        try:
            repo = self.gh.repository(user, repo_name)
            if repo:
                result = repo.delete()
            if not repo or not result:
                raise Exception("Cannot delete: repository {}/{} does not exists.".format(user, repo_name))
        except github3.models.GitHubError as err:
            if err.code == 403:
                raise Exception("You don't have enough permissions for deleting the repository. Check the namespace or the private token's privileges")
            raise Exception("Unhandled exception: {}".format(err))

####################################################################################
# repository_gitlab.py

from gitlab import Gitlab
from gitlab.exceptions import GitlabCreateError, GitlabGetError


@register_target('lab', 'gitlab')
class GitlabService(RepositoryService):
    fqdn = 'gitlab.com'

    def connect(self):
        self.gl = Gitlab(self.url_ro, self._privatekey)

    def create(self, repo):
        repo_name = repo
        if '/' in repo:
            user, repo_name = repo.split('/')
        try:
            self.gl.projects.create(data={
                'name': repo_name,
                # 'namespace_id': user, # TODO does not work, cannot create on
                # another namespace yet
            })
        except GitlabCreateError as err:
            if json.loads(err.response_body.decode('utf-8'))['message']['name'][0] == 'has already been taken':
                raise Exception("Project already exists.")
            else:
                raise Exception("Unhandled error.")
        self.add(user=user, repo=repo_name, default=True)

    def fork(self, user, repo, branch='master'):
        try:
            fork = self.gl.projects.get('{}/{}'.format(user, repo)).forks.create({})
        except GitlabCreateError as err:
            if json.loads(err.response_body.decode('utf-8'))['message']['name'][0] == 'has already been taken':
                raise Exception("Project already exists.")
            else:
                raise Exception("Unhandled error.")
        self.add(user=user, repo=repo, name='upstream', alone=True)
        remote = self.add(repo=fork.name, user=fork.namespace['path'], default=True)
        self.pull(remote, branch)
        log.info("New forked repository available at {}/{}".format(self.url_ro,
                                                                   fork.full_name))

    def delete(self, repo_name, user=None):
        if not user:
            raise Exception('Need an user namespace')
        try:
            repo = self.gl.projects.get('{}/{}'.format(user, repo_name))
            if repo:
                result = repo.delete()
            if not repo or not result:
                raise Exception("Cannot delete: repository {}/{} does not exists.".format(user, repo_name))
        except GitlabGetError as err:
            if err.response_code == 404:
                raise Exception("Cannot delete: repository {}/{} does not exists.".format(user, repo_name))
            elif err.response_code == 403:
                raise Exception("You don't have enough permissions for deleting the repository. Check the namespace or the private token's privileges")
        except Exception as err:
            raise Exception("Unhandled exception: {}".format(err))


####################################################################################


def main(args):
    try:
        if args['--verbose'] >= 3:  # -vvv
            print(args)
        if args['--verbose'] >= 2:  # -vv
            git.Git.GIT_PYTHON_TRACE = True
        if args['--verbose'] >= 1:  # -v
            log.setLevel(logging.DEBUG)
        else:
            log.setLevel(logging.INFO)

        log.removeHandler(logging.NullHandler())
        log.addHandler(logging.StreamHandler())

        if args['--path'] != '.':
            raise Exception('--path option not yet supported.')

        # FIXME workaround for default value that is not correctly parsed in docopt
        if args['<branch>'] == None:
            args['<branch>'] = 'master'

        if args['create'] or args['add'] or args['delete']:
            repository = Repo()
            service = RepositoryService.get_service(repository, args['<target>'])

            if args['create']:
                service.create(args['<user>/<repo>'])
                log.info('Successfully created remote repository `{}/{}`, with local remote `{}`'.format(
                    service.format_path(args['<user>/<repo>']),
                    service.name)
                )

            elif args['add']:
                service.add(args['<user>/<repo>'])
                log.info('Successfully added `{}` as remote named `{}`'.format(
                    args['<user>/<repo>'],
                    service.name)
                )

            elif args['delete']:
                if not args['--force']:
                    ans = input('Are you sure you want to delete the repository {} from the server?\n[yN]> '.format(args['<user>/<repo>']))
                    if 'y' in ans:
                        ans = input('Are you really sure, there\'s no coming back?\n[type \'burn!\' to proceed]> ')
                        if 'burn!' != ans:
                            return 0
                    else:
                        return 0

                if '/' in args['<user>/<repo>']:
                    user, repo = args['<user>/<repo>'].split('/')
                    service.delete(repo, user)
                else:
                    service.delete(repo)
                log.info('Successfully deleted remote `{}` from {}'.format(
                    args['<user>/<repo>'],
                    service.name)
                )
            return 0

        elif args['fork']:
            user, repo_name = args['<user>/<repo>'].split('/')
            if not os.path.exists(repo_name):
                repository = Repo.init(repo_name)
                service = RepositoryService.get_service(repository, args['<target>'])
                service.fork(user, repo_name, branch=args['<branch>'])
                log.info('Successfully cloned repository {} in ./{}'.format(
                    args['<user>/<repo>'],
                    repo_name)
                )

                return 0
            else:
                raise Exception('Cannot clone repository, a folder named {} already exists!'.format(repo_name))

        elif args['clone']:
            user, repo_name = args['<user>/<repo>'].split('/')
            repository = Repo.init(repo_name)
            service = RepositoryService.get_service(repository, args['<target>'])
            service.clone(user, repo_name, args['<branch>'])
            log.info('Successfully cloned `{}` into `./{}`!'.format(
                service.format_path(args['<user>/<repo>']),
                repo_name)
            )
            return 0

        elif args['open']:
            try:
                repository = Repo()
            except:
                repository = None
            RepositoryService.get_service(repository, args['<target>']).open(args['<user>/<repo>'])
            return 0

        log.error('Unknown action.')
        log.error('Please consult help page (--help).')
        return 1
    except Exception as err:
        log.error('Fatal error: {}'.format(err))
        if log.level == logging.DEBUG:
            log.exception('------------------------------------')
        return 2


def cli():
    sys.exit(main(docopt(__doc__.format(self=sys.argv[0], version=__version__))))

if __name__ == '__main__':
    cli()
