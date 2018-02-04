#!/usr/bin/env python3

'''
Usage:
    {self} [--path=<path>] [-v...] <target> fork [--branch=<branch>]
    {self} [--path=<path>] [-v...] <target> create [--add]
    {self} [--path=<path>] [-v...] <target> delete [-f]
    {self} [--path=<path>] [-v...] <target> open
    {self} [--path=<path>] [-v...] <target> (list|ls) [-l] <user>
    {self} [--path=<path>] [-v...] <target> fork <namespace>/<repo> [--branch=<branch>]
    {self} [--path=<path>] [-v...] <target> fork <namespace>/<repo> <repo> [--branch=<branch>]
    {self} [--path=<path>] [-v...] <target> create <namespace>/<repo> [--add]
    {self} [--path=<path>] [-v...] <target> delete <namespace>/<repo> [-f]
    {self} [--path=<path>] [-v...] <target> open <namespace>/<repo>
    {self} [--path=<path>] [-v...] <target> clone <namespace>/<repo> [<repo> [<branch>]]
    {self} [--path=<path>] [-v...] <target> add
    {self} [--path=<path>] [-v...] <target> add <namespace>/<repo> [<name>] [--tracking=<branch>] [-a]
    {self} [--path=<path>] [-v...] <target> request (list|ls)
    {self} [--path=<path>] [-v...] <target> request fetch <request> [-f]
    {self} [--path=<path>] [-v...] <target> request create [--title=<title>] [--message=<message>]
    {self} [--path=<path>] [-v...] <target> request create <local_branch> [--title=<title>] [--message=<message>]
    {self} [--path=<path>] [-v...] <target> request create <remote_branch> <local_branch> [--title=<title>] [--message=<message>]
    {self} [--path=<path>] [-v...] <target> request <namespace>/<repo> (list|ls)
    {self} [--path=<path>] [-v...] <target> request <namespace>/<repo> fetch <request> [-f]
    {self} [--path=<path>] [-v...] <target> request <namespace>/<repo> create [--title=<title>] [--branch=<remote>] [--message=<message>]
    {self} [--path=<path>] [-v...] <target> request <namespace>/<repo> create <local_branch> [--title=<title>] [--branch=<remote>] [--message=<message>]
    {self} [--path=<path>] [-v...] <target> request <namespace>/<repo> create <remote_branch> <local_branch> [--title=<title>] [--branch=<remote>] [--message=<message>]
    {self} [--path=<path>] [-v...] <target> (gist|snippet) (list|ls) [<gist>]
    {self} [--path=<path>] [-v...] <target> (gist|snippet) clone <gist>
    {self} [--path=<path>] [-v...] <target> (gist|snippet) fetch <gist> [<gist_file>]
    {self} [--path=<path>] [-v...] <target> (gist|snippet) create [--secret] <description> [<gist_path> <gist_path>...]
    {self} [--path=<path>] [-v...] <target> (gist|snippet) delete <gist> [-f]
    {self} [--path=<path>] [-v...] <target> config [--config=<gitconfig>]
    {self} [-v...] config [--config=<gitconfig>]
    {self} --help

Tool for managing remote repository services.

Commands:
    add                      Add the service as a remote on this repository
    clone                    Clones this repository from the service
    fork                     Fork (and clone) the repository from the service
    create                   Make this repository a new remote on the service
    delete                   Delete the remote repository
    list                     Lists the repositories for a given user
    gist                     Manages gist files
    request                  Handles requests for merge
    open                     Open the given or current repository in a browser
    config                   Run authentication process and configure the tool

Options:
    <namespace>/<repo>       Repository to work with
    -p,--path=<path>         Path to work on [default: .]
    -v,--verbose             Makes it more chatty (repeat twice to see git commands)
    -h,--help                Shows this message

Options for list:
    <namespace>              Name of the user whose repositories will be listed
    -l,--long                Show one repository per line, when set show the results
                             with the following columns:
    STATUS, COMMITS, REQUESTS, ISSUES, FORKS, CONTRIBUTORS, WATCHERS, LIKES, LANGUAGE, MODIF, NAME

Options for add:
    <name>                   Name to use for the remote (defaults to name of repo)
    -t,--tracking=<branch>   Makes this remote tracking for the current branch
    -a,--alone               Does not add the remote to the 'all' remote

Option for both clone and fork:
    <repo>                   Name of the local workspace directory

Options for clone:
    <branch>                 Branch to pull [default: master]

Options for fork:
    --branch=<branch>        Branch to pull [default: master]

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

Options for request:
    -t,--title=<title>       Title to give to the request for merge
    -m,--message=<message>   Description for the request for merge

Configuration options:
    alias                    Name to use for the git remote
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

{self} version {version}, Copyright ©2016 Bernard `Guyzmo` Pratz
{self} comes with ABSOLUTELY NO WARRANTY; for more informations
read the LICENSE file available in the sources, or check
out: http://www.gnu.org/licenses/gpl-2.0.txt
'''

from docopt import docopt
from getpass import getpass

import os
import sys
import json
import shutil
import logging
import pkg_resources

__version__ = pkg_resources.require('git-repo')[0].version
__author__ = 'Bernard `Guyzmo` Pratz <guyzmo+git_repo@m0g.net>'
__contributors__ = []

log_root = logging.getLogger()
log = logging.getLogger('git_repo')

if sys.version_info.major < 3:  # pragma: no cover
    print('Please use with python version 3')
    sys.exit(1)

from .exceptions import ArgumentError, ResourceNotFoundError
from .services.service import RepositoryService, EXTRACT_URL_RE

from .tools import print_tty, print_iter, loop_input, confirm
from .kwargparse import KeywordArgumentParser, store_parameter, register_action

from git import Repo, Git
from git.exc import InvalidGitRepositoryError, NoSuchPathError, BadName

class GitRepoRunner(KeywordArgumentParser):

    def init(self):  # pragma: no cover
        if 'GIT_WORK_TREE' in os.environ.keys() or 'GIT_DIR' in os.environ.keys():
            del os.environ['GIT_WORK_TREE']

    def get_service(self, lookup_repository=True, resolve_targets=None):
        if not lookup_repository:
            service = RepositoryService.get_service(None, self.target)
            service.connect()
        else:
            # Try to resolve existing repository path
            try:
                try:
                    repository = Repo(os.path.join(self.path, self.repo_name or ''), search_parent_directories=True)
                except NoSuchPathError:
                    repository = Repo(self.path, search_parent_directories=True)
            except InvalidGitRepositoryError:
                raise FileNotFoundError('Cannot find path to the repository.')
            service = RepositoryService.get_service(repository, self.target)
            if not self.repo_name:
                repo_slug = RepositoryService.guess_repo_slug(
                        repository, service, resolve_targets
                        )
                if repo_slug:
                    self.set_repo_slug(repo_slug, auto=True)
        return service

    '''Argument storage'''

    @store_parameter('--verbose')
    def set_verbosity(self, verbose):  # pragma: no cover
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

    @store_parameter('<namespace>/<repo>')
    def set_repo_slug(self, repo_slug, auto=False):
        self.repo_slug = EXTRACT_URL_RE.sub('', repo_slug) if repo_slug else repo_slug
        self._auto_slug = auto
        if not self.repo_slug:
            self.namespace = None
            self.repo_name = None
        elif '/' in self.repo_slug:
            # in case a full URL is given as parameter, just extract the slug part.
            *namespace, self.repo_name = self.repo_slug.split('/')
            self.namespace = '/'.join(namespace)

            # This needs to be manually plucked because otherwise it'll be unset for some commands.
            service = RepositoryService.get_service(None, self.target)
            if len(namespace) > service._max_nested_namespaces:
                raise ArgumentError('Too many slashes.'
                                    'The maximum depth of namespaces is: {}'.format(service._max_nested_namespaces))
        else:
            self.namespace = None
            self.repo_name = self.repo_slug

    @store_parameter('<branch>')
    @store_parameter('--branch')
    def set_branch(self, branch):
        # FIXME workaround for default value that is not correctly parsed in docopt
        if branch == None:
            branch = 'master'

        self.branch = branch

    @store_parameter('<repo>')
    def set_target_repo(self, repo):
        self.target_repo = repo

    @store_parameter('<name>')
    def set_name(self, name):
        self.remote_name = name

    @store_parameter('<gist>')
    def set_gist_ref(self, gist):
        self.gist_ref = gist

    @store_parameter('--config')
    def store_gitconfig(self, val):
        self.config = val or RepositoryService.get_config_path()

    '''Actions'''

    @register_action('ls')
    @register_action('list')
    def do_list(self):
        print_iter(self.get_service(False).list(self.user, self.long))
        return 0

    @register_action('add')
    def do_remote_add(self):
        service = self.get_service()
        remote, user, repo = service.add(self.repo_name, self.namespace,
                    name=self.remote_name,
                    tracking=self.tracking,
                    alone=self.alone,
                    auto_slug=self._auto_slug)
        log.info('Successfully added `{}/{}` as remote named `{}`'.format(
            user, repo,
            remote.name)
        )
        return 0

    @register_action('fork')
    def do_fork(self):
        if not self.repo_slug:
            service = self.get_service(lookup_repository=True)
            try:
                repo_path = self.path
                repository = Repo(repo_path)
            except (InvalidGitRepositoryError, NoSuchPathError):
                raise ArgumentError('Path {} is not a git repository'.format(self.path))

        else:
            # git <target> fork <namespace>/<repo>
            if not self.target_repo:
                if not self.namespace:
                    raise ArgumentError('Cannot clone repository, '
                                        'you shall provide either a <namespace>/<repo> parameter '
                                        'or no parameters to fork current repository!')
                service = self.get_service(None)

            # git <target> fork <namespace>/<repo> <path>
            else:
                repo_path = os.path.join(self.path, self.target_repo)
                try:
                    service = RepositoryService.get_service(Repo(repo_path), self.target)
                except (InvalidGitRepositoryError, NoSuchPathError):
                    service = self.get_service(lookup_repository=False)
                    # if the repository does not exists at given path, clone upstream into that path
                    self.do_clone(service, repo_path)

        service.run_fork(self.namespace, self.repo_name, branch=self.branch)

        if not self.repo_slug or self.target_repo:
            log.info('Successfully forked {} as {} within {}.'.format(
                self.repo_slug, '/'.join([service.username, self.repo_name]), repo_path))

        return 0

    @register_action('clone')
    def do_clone(self, service=None, repo_path=None):
        service = service or self.get_service(lookup_repository=False)
        repo_path = repo_path or os.path.join(self.path, self.target_repo or self.repo_name)
        if os.path.exists(repo_path) and os.listdir(repo_path) != []:
            raise FileExistsError('Cannot clone repository, '
                                  'a folder named {} already exists and '
                                  'is not an empty directory!'.format(repo_path))
        try:
            repository = Repo.init(repo_path)
            service = RepositoryService.get_service(repository, self.target)
            service.clone(self.namespace, self.repo_name, self.branch)
            log.info('Successfully cloned `{}` into `{}`!'.format(
                service.format_path(self.repo_slug),
                repo_path)
            )
            return 0
        except Exception as err:
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
            raise ResourceNotFoundError(err.args[2].decode('utf-8')) from err

    @register_action('create')
    def do_create(self):
        service = self.get_service(lookup_repository=self.repo_slug == None or self.add)
        # if no repo_slug has been given, use the directory name as current project name
        if not self.namespace and not self.repo_name:
            self.set_repo_slug('/'.join([service.user,
                os.path.basename(os.path.abspath(self.path))]))
        if not self.namespace:
            self.namespace = service.user
        service.create(self.namespace, self.repo_name, add=self.add)
        log.info('Successfully created remote repository `{}`, '
                 'with local remote `{}`'.format(
            service.format_path(self.repo_name, namespace=self.namespace),
            service.name)
        )
        return 0

    @register_action('delete')
    def do_delete(self):
        service = self.get_service(lookup_repository=self.repo_slug == None)
        if not self.force:  # pragma: no cover
            if not confirm('repository', self.repo_slug):
                return 0

        if self.namespace:
            service.delete(self.repo_name, self.namespace)
        else:
            service.delete(self.repo_name)
        log.info('Successfully deleted remote `{}` from {}'.format(
            self.repo_slug,
            service.name)
        )
        return 0


    @register_action('open')
    def do_open(self):
        self.get_service(lookup_repository=self.repo_slug is None).open(self.namespace, self.repo_name)
        return 0

    @register_action('request', 'ls')
    @register_action('request', 'list')
    def do_request_list(self):
        service = self.get_service(lookup_repository=self.repo_slug == None)
        print_tty('List of open requests to merge:')
        print_iter(service.request_list(self.namespace, self.repo_name))
        return 0

    @register_action('request', 'create')
    def do_request_create(self):
        def request_edition(repository, from_branch, onto_target):
            try:
                commit = repository.commit(from_branch)
                title, *body = commit.message.split('\n')
            except BadName:
                log.error('Couldn\'t find local source branch {}'.format(from_branch))
                return None, None
            from tempfile import NamedTemporaryFile
            from subprocess import call
            with NamedTemporaryFile(
                    prefix='git-repo-issue-',
                    suffix='.md',
                    mode='w+b') as request_file:
                request_file.write((
                    '# Request for Merge Title ##########################\n'
                    '{}\n'
                    '\n'
                    '# Request for Merge Body ###########################\n'
                    '{}\n'
                    '####################################################\n'
                    '## Filled with commit:\n'
                    '## {}\n'
                    '####################################################\n'
                    '## To be applied:\n'
                    '##   from branch: {}\n'
                    '##   onto project: {}\n'
                    '####################################################\n'
                    '## * All lines starting with # will be ignored.\n'
                    '## * First non-ignored line is the title of the request.\n'
                      ).format(title, '\n'.join(body), commit.name_rev, from_branch, onto_target).encode('utf-8'))
                request_file.flush()
                rv = call("{} {}".format(os.environ['EDITOR'], request_file.name), shell=True)
                if rv != 0:
                    raise ArgumentError("Aborting request, as editor exited abnormally.")
                request_file.seek(0)
                request_message = map(lambda l: l.decode('utf-8'),
                        filter(lambda l: not l.strip().startswith(b'#'), request_file.readlines()))
                try:
                    title = next(request_message)
                    body = ''.join(request_message)
                except Exception:
                    raise ResourceError("Format of the request message cannot be parsed.")

                return title, body


        service = self.get_service(resolve_targets=('upstream', '{service}', 'origin'))

        print_iter(service.request_create(
                self.namespace,
                self.repo_name,
                self.local_branch,
                self.remote_branch,
                self.title,
                self.message,
                self._auto_slug,
                request_edition
            )
        )

        return 0

    @register_action('request', 'fetch')
    def do_request_fetch(self):
        service = self.get_service()
        new_branch = service.request_fetch(self.namespace, self.repo_name, self.request, force=self.force)
        log.info('Successfully fetched request id `{}` of `{}` into `{}`!'.format(
            self.request,
            self.repo_slug,
            new_branch)
        )
        return 0

    @register_action('gist', 'ls')
    @register_action('gist', 'list')
    @register_action('snippet', 'ls')
    @register_action('snippet', 'list')
    def do_gist_list(self):
        service = self.get_service(lookup_repository=False)
        print_iter(service.gist_list(self.gist_ref or None))
        return 0

    @register_action('gist', 'clone')
    @register_action('snippet', 'clone')
    def do_gist_clone(self):
        service = self.get_service(lookup_repository=False)
        repo_path = os.path.join(self.path, self.gist_ref.split('/')[-1])
        service.repository = Repo.init(repo_path)
        service.gist_clone(self.gist_ref)
        log.info('Successfully cloned `{}` into `{}`!'.format( self.gist_ref, repo_path))
        return 0

    @register_action('gist', 'fetch')
    @register_action('snippet', 'fetch')
    def do_gist_fetch(self):
        service = self.get_service(lookup_repository=False)
        # send gist to stdout, not using log.info on purpose here!
        print(service.gist_fetch(self.gist_ref, self.gist_file))
        return 0

    @register_action('gist', 'create')
    @register_action('snippet', 'create')
    def do_gist_create(self):
        service = self.get_service(lookup_repository=False)
        url = service.gist_create(self.gist_path, self.description, self.secret)
        log.info('Successfully created gist `{}`!'.format(url))
        return 0

    @register_action('gist', 'delete')
    @register_action('snippet', 'delete')
    def do_gist_delete(self):
        service = self.get_service(lookup_repository=False)
        if not self.force:  # pragma: no cover
            if not confirm('snippet', self.gist_ref):
                return 0

        service.gist_delete(self.gist_ref)
        log.info('Successfully deleted gist!')
        return 0

    @register_action('config')
    def do_config(self):
        def setup_service(service):
            new_conf = dict(
                    fqdn=None,
                    remote=None,
                    )

            print('Is your service self-hosted?')
            if 'y' in input('    [yN]> ').lower():
                new_conf['type'] = service.name
                print('What name do you want to give this service?')
                new_conf['name'] = input('[{}]> '.format(service.name))
                new_conf['command'] = new_conf['name']
                service.name, service.command = new_conf['name'], new_conf['command']
                print('Enter the service\'s domain name:')
                new_conf['fqdn'] = input('[{}]> '.format(service.fqdn))
                print('Enter the service\'s port:')
                new_conf['port'] = input('[443]> ') or '443'
                print('Are you connecting using HTTPS? (you should):')
                if 'n' in input('    [Yn]> ').lower():
                    new_conf['scheme'] = 'http'
                else:
                    new_conf['scheme'] = 'https'
                    print('Do you need to use an insecure connection? (you shouldn\'t):')
                    new_conf['insecure'] = 'y' in input('    [yN]> ').lower()
                    service.session_insecure = new_conf['insecure']
                    if not new_conf['insecure']:
                        print('Do you want to setup the path to custom certificate?:')
                        if 'y' in input('    [yN]> ').lower():
                            new_conf['server-cert'] = loop_input('/path/to/certbundle.pem []> ')
                            service.session_certificate = new_conf['server-cert']

                service.fqdn = new_conf['fqdn']
                service.port = new_conf['port']
                service.scheme = new_conf['scheme']

            conf = service.get_config(self.config)
            if 'token' in conf:
                raise Exception('A token has been generated for this service. Please revoke and delete before proceeding.')

            print('Please enter your credentials to connect to the service:')
            username = loop_input('username> ')
            password = loop_input('password> ', method=getpass)

            new_conf['token'] = service.get_auth_token(username, password, prompt=loop_input)
            print('Great! You\'ve been identified 🍻')

            print('Do you want to give a custom name for this service\'s remote?')
            if 'y' in input('    [yN]> ').lower():
                print('Enter the remote\'s name:')
                new_conf['remote'] = loop_input('[{}]> '.format(service.name))

            print('Do you want to configure a git alias?')
            print('N.B.: instead of typing `git repo {0}` you\'ll be able to type `git {0}`'.format(service.command))
            if 'n' in input('    [Yn]> ').lower():
                set_alias = False
            else:
                set_alias = True

            service.store_config(self.config, **new_conf)
            if set_alias:
                service.set_alias(self.config)

        if self.target:
            services = [self.get_service(lookup_repository=False)]
        else:
            services = RepositoryService.service_map.values()

        for service in sorted(services, key=lambda s: s.name):
            print('Do you want to configure the {} service?'.format(service.name))
            if 'n' in input('    [Yn]> ').lower():
                continue
            setup_service(service)

        print('🍻 The configuration is done!')
        return 0


def main(args):
    try:
        return GitRepoRunner(args).run()
    except Exception as err:
        log.error('Fatal error: {}'.format(err))
        if log_root.level == logging.DEBUG:
            log.exception('------------------------------------')
        return 2


def cli():  # pragma: no cover
    try:
        sys.exit(main(docopt(__doc__.format(self=sys.argv[0].split(os.path.sep)[-1], version=__version__))))
    finally:
        # Whatever happens, make sure that the cursor reappears with some ANSI voodoo
        if sys.stdout.isatty():
            sys.stdout.write('\033[?25h')

if __name__ == '__main__': #pragma: no cover
    cli()
