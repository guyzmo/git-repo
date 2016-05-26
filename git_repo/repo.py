#!/usr/bin/env python

'''
Usage:
    {self} [--path=<path>] [-v...] <target> add <user>/<repo> [<name>] [--tracking=<branch>] [-a]
    {self} [--path=<path>] [-v...] <target> fork <user>/<repo> [<branch>] [--clone]
    {self} [--path=<path>] [-v...] <target> clone <user>/<repo> [<branch>]
    {self} [--path=<path>] [-v...] <target> create <user>/<repo> [--add]
    {self} [--path=<path>] [-v...] <target> delete <user>/<repo> [-f]
    {self} [--path=<path>] [-v...] <target> open
    {self} [--path=<path>] [-v...] <target> open [<user>/<repo>]
    {self} [--path=<path>] [-v...] <target> request (list|ls)
    {self} [--path=<path>] [-v...] <target> request fetch <request>
    {self} [--path=<path>] [-v...] <target> request [<user>/<repo>] (list|ls)
    {self} [--path=<path>] [-v...] <target> request [<user>/<repo>] fetch <request>
    {self} [--path=<path>] [-v...] <target> gist (list|ls) [<gist>]
    {self} [--path=<path>] [-v...] <target> gist clone <gist>
    {self} [--path=<path>] [-v...] <target> gist fetch <gist> [<gist_file>]
    {self} [--path=<path>] [-v...] <target> gist create [--secret] <description> [<gist_path> <gist_path>...]
    {self} [--path=<path>] [-v...] <target> gist delete <gist> [-f]
    {self} --help

Tool for managing remote repository services.

Commands:
    add                      Add the service as a remote on this repository
    clone                    Clones this repository from the service
    fork                     Fork (and clone) the repository from the service
    create                   Make this repository a new remote on the service
    delete                   Delete the remote repository
    gist                     Manages gist files
    request                  Handles requests for merge
    open                     Open the given or current repository in a browser

Options:
    <user>/<repo>            Repository to work with
    -p,--path=<path>         Path to work on [default: .]
    -v,--verbose             Makes it more chatty (repeat twice to see git commands)
    -h,--help                Shows this message

Options for add:
    <name>                   Name to use for the remote (defaults to name of repo)
    -t,--tracking=<branch>   Makes this remote tracking for the current branch
    -a,--alone               Does not add the remote to the 'all' remote

Options for fork and clone:
    <branch>                 Branch to pull (when cloning) [default: master]
    --clone                  Clone locally after fork

Options for create:
    --add                    Add to local repository after creation

Options for delete:
    -f,--force               Do not ask for confirmation

Options for gist:
    <gist>                   Identifier of the gist to fetch
    <gist_file>              Name of the file to fetch
    <gist_path>              Name of the file or directory to use for a new gist.
                             If path is a directory, all files directly within it
                             will be pushed. If a list of path is given, all files
                             from them will be pushed.
    --secret                 Do not publicize gist when pushing

Configuration options:
    alias                    Name to use for the git remote
    url                      URL of the repository
    fqdn                     URL of the repository
    type                     Name of the service to use (github, gitlab, bitbucket)

Configuration example:

[gitrepo "gitlab"]
    token = yourapitoken
    alias = lab

[gitrepo "personal"]
    type = gitlab
    token = yourapitoken
    fqdn = custom.org

{self} version {version}, Copyright ⓒ2016 Bernard `Guyzmo` Pratz
{self} comes with ABSOLUTELY NO WARRANTY; for more informations
read the LICENSE file available in the sources, or check
out: http://www.gnu.org/licenses/gpl-2.0.txt
'''

from docopt import docopt

import os
import sys
import json
import logging
import pkg_resources

__version__ = pkg_resources.require('git-repo')[0].version
__author__ = 'Bernard `Guyzmo` Pratz <guyzmo+git_repo@m0g.net>'
__contributors__ = []

log_root = logging.getLogger()
log = logging.getLogger('git_repo')

if sys.version_info.major < 3: # pragma: no cover
    print('Please use with python version 3')
    sys.exit(1)

from .exceptions import ArgumentError
from .services.service import RepositoryService

from .kwargparse import KeywordArgumentParser, store_parameter, register_action

from git import Repo, Git
from git.exc import InvalidGitRepositoryError, NoSuchPathError

def confirm(what, where):
    '''
    Method to show a CLI based confirmation message, waiting for a yes/no answer.
    "what" and "where" are used to better define the message.
    '''
    ans = input('Are you sure you want to delete the '
                '{} {} from the service?\n[yN]> '.format(what, where))
    if 'y' in ans:
        ans = input('Are you really sure? there\'s no coming back!\n'
                    '[type \'burn!\' to proceed]> ')
        if 'burn!' != ans:
            return False
    else:
        return False
    return True


class GitRepoRunner(KeywordArgumentParser):

    def init(self): # pragma: no cover
        if 'GIT_WORK_TREE' in os.environ.keys() or 'GIT_DIR' in os.environ.keys():
            del os.environ['GIT_WORK_TREE']

    def _guess_repo_slug(self, repository, target):
        config = repository.config_reader()
        for section_name in config.sections():
            if 'remote' in section_name:
                section = dict(config.items(section_name))
                if target in section['url']:
                    if section['url'].startswith('https'):
                        *_, user, name = section['url'].rstrip('.git').split('/')
                        self.set_repo_slug('/'.join([user, name]))
                        break
                    elif section['url'].startswith('git@'):
                        _, repo_slug = section['url'].rstrip('.git').split(':')
                        self.set_repo_slug(repo_slug)
                        break

    def get_service(self, resolve=True):
        if not resolve:
            service = RepositoryService.get_service(None, self.target)
            service.connect()
        else:
            # Try to resolve existing repository path
            try:
                try:
                    repository = Repo(os.path.join(self.path, self.repo_name or ''))
                except NoSuchPathError:
                    repository = Repo(self.path)
            except InvalidGitRepositoryError:
                raise FileNotFoundError('Cannot find path to the repository.')
            service = RepositoryService.get_service(repository, self.target)
            if not self.repo_slug:
                self._guess_repo_slug(repository, service.name)
        return service

    '''Argument storage'''

    @store_parameter('--verbose')
    def set_verbosity(self, verbose): # pragma: no cover
        if verbose >= 5:
            print(self.args)
        if verbose >= 4:
            import http.client
            http.client.HTTPConnection.debuglevel = 1
            logging.getLogger("requests.packages.urllib3").setLevel(logging.DEBUG)
            logging.getLogger("requests.packages.urllib3").propagate = True
        if verbose >= 3:
            Git.GIT_PYTHON_TRACE = 'full'
        if verbose >= 2:
            Git.GIT_PYTHON_TRACE = True
            FORMAT = '> %(message)s'
            formatter = logging.Formatter(fmt=FORMAT)
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            logging.getLogger('git.cmd').removeHandler(logging.NullHandler())
            logging.getLogger('git.cmd').addHandler(handler)
        if verbose >= 1:
            log_root.setLevel(logging.DEBUG)
        else:
            log_root.setLevel(logging.INFO)

        log.addHandler(logging.StreamHandler())

    @store_parameter('<user>/<repo>')
    def set_repo_slug(self, repo_slug):
        self.repo_slug = repo_slug
        if not repo_slug:
            self.user_name = None
            self.repo_name = None
        elif '/' in repo_slug:
            self.user_name, self.repo_name, *overflow = repo_slug.split('/')
            if len(overflow) != 0:
                raise ArgumentError('Too many slashes.'
                                    'Format of the parameter is <user>/<repo> or <repo>.')
        else:
            self.user_name = None
            self.repo_name = repo_slug

    @store_parameter('<branch>')
    def set_branch(self, branch):
        # FIXME workaround for default value that is not correctly parsed in docopt
        if branch == None:
            branch = 'master'

        self.branch = branch

    @store_parameter('<name>')
    def set_name(self, name):
        self.remote_name = name

    @store_parameter('<gist>')
    def set_gist_ref(self, gist):
        self.gist_ref = gist

    '''Actions'''

    @register_action('add')
    def do_remote_add(self):
        service = self.get_service()
        service.add(self.repo_name, self.user_name,
                    name=self.remote_name,
                    tracking=self.tracking,
                    alone=self.alone)
        log.info('Successfully added `{}` as remote named `{}`'.format(
            self.repo_slug,
            service.name)
        )
        return 0

    @register_action('fork')
    def do_fork(self):
        service = self.get_service(resolve=False)
        if not os.path.exists(self.repo_name):
            repo_path = os.path.join(self.path, self.repo_name)
            repository = Repo.init(repo_path)
            service = RepositoryService.get_service(repository, self.target)
            service.fork(self.user_name, self.repo_name, branch=self.branch, clone=self.clone)
            log.info('Successfully cloned repository {} in {}'.format(
                self.repo_slug,
                repo_path)
            )

            return 0
        else:
            raise FileExistsError('Cannot clone repository, '
                                  'a folder named {} already exists!'.format(self.repo_name))

    @register_action('clone')
    def do_clone(self):
        service = self.get_service(resolve=False)
        repo_path = os.path.join(self.path, self.repo_name)
        repository = Repo.init(repo_path)
        service = RepositoryService.get_service(repository, self.target)
        service.clone(self.user_name, self.repo_name, self.branch)
        log.info('Successfully cloned `{}` into `{}`!'.format(
            service.format_path(self.repo_slug),
            repo_path)
        )
        return 0

    @register_action('create')
    def do_create(self):
        service = self.get_service()
        service.create(self.user_name, self.repo_name, add=self.add)
        log.info('Successfully created remote repository `{}`, '
                 'with local remote `{}`'.format(
            service.format_path(self.repo_name, namespace=self.user_name),
            service.name)
        )
        return 0

    @register_action('delete')
    def do_delete(self):
        service = self.get_service()
        if not self.force: # pragma: no cover
            if not confirm('repository', self.repo_slug):
                return 0

        if self.user_name:
            service.delete(self.repo_name, self.user_name)
        else:
            service.delete(self.repo_name)
        log.info('Successfully deleted remote `{}` from {}'.format(
            self.repo_slug,
            service.name)
        )
        return 0


    @register_action('open')
    def do_open(self):
        self.get_service(resolve=self.repo_slug is None).open(self.user_name, self.repo_name)
        return 0

    @register_action('request', 'ls')
    @register_action('request', 'list')
    def do_request_list(self):
        service = self.get_service()
        log.info('List of open requests to merge:')
        log.info(" {}\t{}\t{}".format('id', 'title'.ljust(60), 'URL'))
        for pr in service.request_list(self.user_name, self.repo_name):
            print("{}\t{}\t{}".format(pr[0].rjust(3), pr[1][:60].ljust(60), pr[2]))
        return 0

    @register_action('request', 'fetch')
    def do_request_fetch(self):
        service = self.get_service()
        new_branch = service.request_fetch(self.user_name, self.repo_name, self.request)
        log.info('Successfully fetched request id `{}` of `{}` into `{}`!'.format(
            self.request,
            self.repo_slug,
            new_branch)
        )
        return 0

    @register_action('gist', 'ls')
    @register_action('gist', 'list')
    def do_gist_list(self):
        service = self.get_service(resolve=False)
        if self.gist_ref:
            log.info("{:15}\t{:>7}\t{}".format('language', 'size', 'name'))
            for gist_file in service.gist_list(self.gist_ref):
                print("{:15}\t{:7}\t{}".format(*gist_file))
        else:
            log.info("{:56}\t{}".format('id', 'title'.ljust(60)))
            for gist in service.gist_list():
                print( "{:56}\t{}".format(gist[0], gist[1]))
        return 0

    @register_action('gist', 'clone')
    def do_gist_clone(self):
        service = self.get_service(resolve=False)
        repo_path = os.path.join(self.path, self.gist_ref.split('/')[-1])
        service.repository = Repo.init(repo_path)
        service.gist_clone(self.gist_ref)
        log.info('Successfully cloned `{}` into `{}`!'.format( self.gist_ref, repo_path))
        return 0

    @register_action('gist', 'fetch')
    def do_gist_fetch(self):
        service = self.get_service(resolve=False)
        # send gist to stdout, not using log.info on purpose here!
        print(service.gist_fetch(self.gist_ref, self.gist_file))
        return 0

    @register_action('gist', 'create')
    def do_gist_create(self):
        service = self.get_service(resolve=False)
        url = service.gist_create(self.gist_path, self.description, self.secret)
        log.info('Successfully created gist `{}`!'.format(url))
        return 0

    @register_action('gist', 'delete')
    def do_gist_delete(self):
        service = self.get_service(resolve=False)
        if not self.force: # pragma: no cover
            if not confirm('gist', self.gist_ref):
                return 0

        service.gist_delete(self.gist_ref)
        log.info('Successfully deleted gist!')
        return 0


def main(args):
    try:
        return GitRepoRunner(args).run()
    except Exception as err:
        log.error('Fatal error: {}'.format(err))
        if log_root.level == logging.DEBUG:
            log.exception('------------------------------------')
        return 2



def cli(): #pragma: no cover
    sys.exit(main(docopt(__doc__.format(self=sys.argv[0], version=__version__))))

if __name__ == '__main__': #pragma: no cover
    cli()
