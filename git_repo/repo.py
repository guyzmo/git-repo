#!/usr/bin/env python

'''
Usage:
    {self} [--path=<path>] [-v -v...] <target> add <user>/<repo> [<name>] [--tracking=<branch>] [-a]
    {self} [--path=<path>] [-v -v...] <target> fork <user>/<repo> [<branch>] [--clone]
    {self} [--path=<path>] [-v -v...] <target> clone <user>/<repo> [<branch>]
    {self} [--path=<path>] [-v -v...] <target> create <user>/<repo> [--add]
    {self} [--path=<path>] [-v -v...] <target> delete <user>/<repo> [-f]
    {self} [--path=<path>] [-v -v...] <target> open [<user>/<repo>]
    {self} --help

Tool for managing remote repository services.

Commands:
    add                      Add the service as a remote on this repository
    clone                    Clones this repository from the service
    fork                     Fork (and clone) the repository from the service
    create                   Make this repository a new remote on the service
    delete                   Delete the remote repository
    open                     Open the given or current repository in a browser

Options:
    <user>/<repo>            Repository to work with
    <branch>                 Branch to pull (when cloning) [default: master]
    -p,--path=<path>         Path to work on [default: .]
    -f,--force               Do not ask for confirmation
    --clone                  Clone locally after fork
    --add                    Add to local repository after creation
    -v,--verbose             Makes it more chatty (repeat twice to see git commands)
    -h,--help                Shows this message

Options for add:
    <name>                   Name to use for the remote (defaults to name of repo)
    -t,--tracking <branch>   Makes this remote tracking for the current branch
    -a,--alone               Does not add the remote to the 'all' remote

Configuration options:
    alias                    Name to use for the git remote
    url                      URL of the repository
    private-key              Private key to use for connecting to the service
    type                     Name of the service to use (github, gitlab, bitbucket)

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

from git import Repo, Git
from git.exc import InvalidGitRepositoryError, NoSuchPathError

def main(args):
    try:
        if args['--verbose'] >= 4:  # pragma: no cover
            import http.client
            http.client.HTTPConnection.debuglevel = 1
            logging.getLogger("requests.packages.urllib3").setLevel(logging.DEBUG)
            logging.getLogger("requests.packages.urllib3").propagate = True
        if args['--verbose'] >= 3: # pragma: no cover
            print(args)
        if args['--verbose'] >= 2: # pragma: no cover
            Git.GIT_PYTHON_TRACE = True
            FORMAT = '> %(message)s'
            formatter = logging.Formatter(fmt=FORMAT)
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            logging.getLogger('git.cmd').removeHandler(logging.NullHandler())
            logging.getLogger('git.cmd').addHandler(handler)
        if args['--verbose'] >= 1: # pragma: no cover
            log_root.setLevel(logging.DEBUG)
        else: #pragma: no cover
            log_root.setLevel(logging.INFO)

        log.addHandler(logging.StreamHandler())

        # FIXME workaround for default value that is not correctly parsed in docopt
        if args['<branch>'] == None:
            args['<branch>'] = 'master'

        if 'GIT_WORK_TREE' in os.environ.keys() or 'GIT_DIR' in os.environ.keys(): #pragma: no cover
            del os.environ['GIT_WORK_TREE']

        if '/' in args['<user>/<repo>']:
            if len(args['<user>/<repo>'].split('/')) > 2:
                raise ArgumentError('Too many slashes.'
                                    'Format of the parameter is <user>/<repo> or <repo>.')
            user, repo = args['<user>/<repo>'].split('/')
        else:
            user = None
            repo = args['<user>/<repo>']

        if args['create'] or args['add'] or args['delete'] or args['open']:
            # Try to resolve existing repository path
            try:
                try:
                    repository = Repo(os.path.join(args['--path'], repo))
                except NoSuchPathError:
                    repository = Repo(args['--path'])
            except InvalidGitRepositoryError:
                raise FileNotFoundError('Cannot find path to the repository.')
            service = RepositoryService.get_service(repository, args['<target>'])

            if args['create']:
                service.create(user, repo, add=args['--add'])
                log.info('Successfully created remote repository `{}`, '
                         'with local remote `{}`'.format(
                    service.format_path(repo, namespace=user),
                    service.name)
                )

            elif args['add']:
                service.add(repo, user,
                            name=args['<name>'],
                            tracking=args['--tracking'],
                            alone=args['--alone'])
                log.info('Successfully added `{}` as remote named `{}`'.format(
                    args['<user>/<repo>'],
                    service.name)
                )

            elif args['delete']:
                if not args['--force']: # pragma: no cover
                    ans = input('Are you sure you want to delete the repository '
                                '{} from the server?\n[yN]> '.format(args['<user>/<repo>']))
                    if 'y' in ans:
                        ans = input('Are you really sure? there\'s no coming back!\n'
                                    '[type \'burn!\' to proceed]> ')
                        if 'burn!' != ans:
                            return 0
                    else:
                        return 0

                if user:
                    service.delete(repo, user)
                else:
                    service.delete(repo)
                log.info('Successfully deleted remote `{}` from {}'.format(
                    args['<user>/<repo>'],
                    service.name)
                )

            elif args['open']:
                RepositoryService.get_service(None, args['<target>']).open(user, repo)

            return 0

        elif args['fork']:
            if not os.path.exists(repo):
                repo_path = os.path.join(args['--path'], repo)
                repository = Repo.init(repo_path)
                service = RepositoryService.get_service(repository, args['<target>'])
                service.fork(user, repo, branch=args['<branch>'], clone=args['--clone'])
                log.info('Successfully cloned repository {} in {}'.format(
                    args['<user>/<repo>'],
                    repo_path)
                )

                return 0
            else:
                raise FileExistsError('Cannot clone repository, '
                                      'a folder named {} already exists!'.format(repo))

        elif args['clone']:
            repo_path = os.path.join(args['--path'], repo)
            repository = Repo.init(repo_path)
            service = RepositoryService.get_service(repository, args['<target>'])
            service.clone(user, repo, args['<branch>'])
            log.info('Successfully cloned `{}` into `{}`!'.format(
                service.format_path(args['<user>/<repo>']),
                repo_path)
            )
            return 0

        log.error('Unknown action.')
        log.error('Please consult help page (--help).')
        return 1
    except Exception as err:
        log.error('Fatal error: {}'.format(err))
        if log_root.level == logging.DEBUG:
            log.exception('------------------------------------')
        return 2


def cli(): #pragma: no cover
    sys.exit(main(docopt(__doc__.format(self=sys.argv[0], version=__version__))))

if __name__ == '__main__': #pragma: no cover
    cli()
