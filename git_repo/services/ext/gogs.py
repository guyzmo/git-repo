#!/usr/bin/env python
import sys
import logging
log = logging.getLogger('git_repo.gogs')

from ..service import register_target, RepositoryService, os
from ...exceptions import ResourceError, ResourceExistsError, ResourceNotFoundError

import gogs_client
import requests
from urllib.parse import urlparse, urlunparse
import functools

from git import config as git_config
from git.exc import GitCommandError

@register_target('gg', 'gogs')
class GogsService(RepositoryService):
    fqdn = 'try.gogs.io'
    #fqdn = 'http://127.0.0.1:3000'
    gg = None

    def __init__(self, *args, **kwargs):
        self.session = requests.Session()
        RepositoryService.__init__(self, *args, **kwargs)
        self.ensure_init()

    def ensure_init(self):
        if self.gg is not None:
            return
        self.url_base, self.fqdn = self._url_parse(self.fqdn)
        if 'insecure' not in self.config:
            self.insecure = self.fqdn != 'try.gogs.io'
        self.session.verify = not self.insecure
        if 'server-cert' in self.config:
            self.session.verify = self.config['server-cert']
        self.default_private = self.config.get('default-private', 'false').lower() not in ('0','no','false')
        self.ssh_url = self.config.get('ssh-url', None) or self.fqdn
        if not self.repository:
            config = git_config.GitConfigParser(os.path.join(os.environ['HOME'], '.gitconfig'), True)
        else:
            config = self.repository.config_reader()
        proxies = {}
        for scheme in 'http https'.split():
            proxy = config.get_value(scheme, 'proxy', '')
            if proxy:
                proxies[scheme] = proxy
        self.session.proxies.update(proxies)
        self.gg = gogs_client.GogsApi(self.url_base, self.session)
        #if ':' in self._privatekey:
        #    self.auth = gogs_client.UsernamePassword(*self._privatekey.split(':',1))
        #else:
        self.auth = gogs_client.Token(self._privatekey)

    @classmethod
    def _url_parse(cls, url):
        if '://' not in url:
            url = 'https://'+url
        parse = urlparse(url)
        url_base = urlunparse((parse.scheme, parse.netloc)+('',)*4)
        fqdn = parse.hostname
        return url_base, fqdn

    @property
    def url_ro(self):
        return self.url_base

    @property
    def url_rw(self):
        url = self.ssh_url
        if '@' in url:
            return url
        return '@'.join([self.git_user, url])

    @classmethod
    def get_auth_token(cls, login, password, prompt=None):
        import platform
        name = 'git-repo2 token used on {}'.format(platform.node())
        if '/' in login:
            url, login = login.rsplit('/', 1)
        else:
            url = input('URL [{}]> '.format(cls.fqdn)) or cls.fqdn
        url_base, fqdn = cls._url_parse(url)
        gg = gogs_client.GogsApi(url_base)
        auth = gogs_client.UsernamePassword(login, password)
        tokens = gg.get_tokens(auth, login)
        tokens = dict((token.name, token.token) for token in tokens)
        if name in tokens:
            return tokens[name]
        if 'git-repo2 token' in tokens:
            return tokens['git-repo2 token']
        token = gg.create_token(auth, name, login)
        return token.token

    @property
    def user(self):
        return self.gg.authenticated_user(self.auth).username

    def orgs(self):
        orgs = self.gg._check_ok(self.gg._get('/user/orgs', auth=self.auth)).json()
        #return [gogs_client.GogsUser.from_json(org) for org in orgs]
        return [org['username'] for org in orgs]

    def connect(self):
        self.ensure_init()
        try:
            if self.insecure:
                try:
                    try:
                        urllib3 = requests.packages.urllib3
                    except Exception:
                        import urllib3
                    urllib3.disable_warnings()
                except ImportError:
                    pass
            self.username = self.user  # Call to self.gg.authenticated_user()
        except requests.HTTPError as err:
            if err.response is not None and err.response.status_code == 401:
                if not self._privatekey:
                    raise ConnectionError('Could not connect to GoGS. '
                                          'Please configure .gitconfig '
                                          'with your gogs private key.') from err
                else:
                    raise ConnectionError('Could not connect to GoGS. '
                                          'Check your configuration and try again.') from err
            else:
                raise err

    def create(self, user, repo, add=False):
        try:
            if user == self.username:
                repository = self.gg.create_repo(self.auth, name=repo, private=self.default_private)
            elif user in self.orgs():
                data = dict(name=repo, private=self.default_private)
                response = self.gg._post('/org/{}/repos'.format(user), auth=self.auth, data=data)
                repository = gogs_client.GogsRepo.from_json(self.gg._check_ok(response).json())
            else:
                data = dict(name=repo, private=self.default_private)
                response = self.gg._post('/admin/users/{}/repos'.format(user), auth=self.auth, data=data)
                repository = gogs_client.GogsRepo.from_json(self.gg._check_ok(response).json())
        except gogs_client.ApiFailure as err:
            if err.status_code == 422:
                raise ResourceExistsError("Project already exists.") from err
            else:
                raise ResourceError("Unhandled error.") from err
        except Exception as err:
            raise ResourceError("Unhandled exception: {}".format(err)) from err
        if add:
            self.add(user=self.username, repo=repo, tracking=self.name)

    def fork(self, user, repo):
        raise NotImplementedError

    def delete(self, repo, user=None):
        if not user:
            user = self.username
        try:
            self.gg.delete_repo(self.auth, user, repo)
        except gogs_client.ApiFailure as err:
            if err.status_code == 404:
                raise ResourceNotFoundError("Cannot delete: repository {}/{} does not exists.".format(user, repo)) from err
            elif err.status_code == 403:
                raise ResourcePermissionError("You don't have enough permissions for deleting the repository. Check the namespace or the private token's privileges") from err
            elif err.status_code == 422:
                raise ResourceNotFoundError("Cannot delete repository {}/{}: user {} does not exists.".format(user, repo, user)) from err
            raise ResourceError("Unhandled error: {}".format(err)) from err
        except Exception as err:
            raise ResourceError("Unhandled exception: {}".format(err)) from err

    def list(self, user, _long=False):
        import shutil, sys
        from datetime import datetime
        term_width = shutil.get_terminal_size((80, 20)).columns
        def col_print(lines, indent=0, pad=2):
            # prints a list of items in a fashion similar to the dir command
            # borrowed from https://gist.github.com/critiqjo/2ca84db26daaeb1715e1
            n_lines = len(lines)
            if n_lines == 0:
                return
            col_width = max(len(line) for line in lines)
            n_cols = int((term_width + pad - indent)/(col_width + pad))
            n_cols = min(n_lines, max(1, n_cols))
            col_len = int(n_lines/n_cols) + (0 if n_lines % n_cols == 0 else 1)
            if (n_cols - 1) * col_len >= n_lines:
                n_cols -= 1
            cols = [lines[i*col_len : i*col_len + col_len] for i in range(n_cols)]
            rows = list(zip(*cols))
            rows_missed = zip(*[col[len(rows):] for col in cols[:-1]])
            rows.extend(rows_missed)
            for row in rows:
                print(" "*indent + (" "*pad).join(line.ljust(col_width) for line in row))

        r = self.gg._get('/user/repos', auth=self.auth)
        repositories = self.gg._check_ok(r).json()
        repositories = [repo for repo in repositories if repo['owner']['username'] == user]
        if user != self.username and not repositories and user not in self.orgs:
            raise ResourceNotFoundError("Unable to list namespace {} - only authenticated user and orgs available for listing.".format(user))
        if not _long:
            col_print([repo['full_name'] for repo in repositories])
        else:
            print('Status\tCommits\tReqs\tIssues\tForks\tCoders\tWatch\tLikes\tLang\tModif\t\t\t\tName', file=sys.stderr)
            for repo in repositories:
                status = ''.join([
                    'F' if repo['fork'] else ' ',          # is a fork?
                    'P' if repo['private'] else ' ',       # is private?
                ])
                try:
                    issues = self.gg._check_ok(self.gg._get('/repos/{}/issues'.format(repo['full_name']), auth=self.auth)).json()
                except Exception:
                    issues = []
                print('\t'.join([
                    # status
                    status,
                    # stats
                    str(len(list(()))),                    # number of commits
                    str(len(list(()))),                    # number of pulls
                    str(len(list(issues))),                # number of issues
                    str(repo.get('forks_count') or 0),     # number of forks
                    str(len(list(()))),                    # number of contributors
                    str(repo.get('watchers_count') or 0),  # number of subscribers
                    str(repo.get('stars_count') or 0),     # number of ♥
                    # info
                    repo.get('language') or '?',           # language
                    repo['updated_at'],                    # date
                    repo['full_name'],                     # name
                ]))

    def get_repository(self, user, repo):
        try:
            return self.gg.get_repo(self.auth, user, repo)
        except gogs_client.ApiFailure as err:
            if err.status_code == 404:
                raise ResourceNotFoundError("Cannot get: repository {}/{} does not exists.".format(user, repo)) from err
            raise ResourceError("Unhandled error: {}".format(err)) from err
        except Exception as err:
            raise ResourceError("Unhandled exception: {}".format(err)) from err

    def gist_list(self, gist=None):
        raise NotImplementedError

    def gist_fetch(self, gist, fname=None):
        raise NotImplementedError

    def gist_clone(self, gist):
        raise NotImplementedError

    def gist_create(self, gist_pathes, description, secret=False):
        raise NotImplementedError

    def gist_delete(self, gist_id):
        raise NotImplementedError

    def request_create(self, user, repo, local_branch, remote_branch, title, description=None):
        raise NotImplementedError

    def request_list(self, user, repo):
        raise NotImplementedError

    def request_fetch(self, user, repo, request, pull=False):
        raise NotImplementedError
