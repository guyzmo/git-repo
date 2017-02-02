#!/usr/bin/env python
import sys
import logging
log = logging.getLogger('git_repo.gogs')

from ..service import register_target, RepositoryService, os
from ...exceptions import ResourceError, ResourceExistsError, ResourceNotFoundError

from gogs_client import GogsApi, GogsRepo, Token, UsernamePassword, ApiFailure
from requests import Session, HTTPError
from urllib.parse import urlparse, urlunparse
import functools

from git import config as git_config
from git.exc import GitCommandError

class GogsClient(GogsApi):
    def __init__(self):
        self.session = Session()

    def setup(self, *args, **kwarg):
        super().__init__(*args, session=self.session, **kwarg)

    def set_token(self, token):
        self.auth = Token(token)

    def set_default_private(self, p):
        self.default_private = p

    def setup_session(self, ssl_config, proxy=dict()):
        self.session.verify = ssl_config
        self.session.proxies.update(proxy)

    @property
    def username(self):
        if not hasattr(self, '_username'):
            self._username = self.authenticated_user(self.auth).username
        return self._username

    def orgs(self):
        orgs = self._check_ok(self._get('/user/orgs', auth=self.auth)).json()
        #return [gogs_client.GogsUser.from_json(org) for org in orgs]
        return [org['username'] for org in orgs]

    def create_repository(self, user, repo):
        if user == self.username:
            repository = self.create_repo(self.auth, name=repo, private=self.default_private)
        elif user in self.orgs():
            data = dict(name=repo, private=self.default_private)
            response = self._post('/org/{}/repos'.format(user), auth=self.auth, data=data)
            repository = GogsRepo.from_json(self._check_ok(response).json())
        else:
            data = dict(name=repo, private=self.default_private)
            response = self._post('/admin/users/{}/repos'.format(user), auth=self.auth, data=data)
            repository = GogsRepo.from_json(self._check_ok(response).json())

    def delete_repository(self, user, repo):
        return self.delete_repo(self.auth, user, repo)

    def repository(self, user, repo):
        return self.get_repo(self.auth, user, repo)

    def repositories(self, user):
        r = self._get('/user/repos', auth=self.auth)
        repositories = self._check_ok(r).json()
        repositories = [repo for repo in repositories if repo['owner']['username'] == user]
        return repositories

@register_target('gg', 'gogs')
class GogsService(RepositoryService):
    fqdn = 'try.gogs.io'

    def __init__(self, *args, **kwargs):
        self.gg = GogsClient()

        super().__init__(*args, **kwargs)

        self.gg.setup(self.url_ro)
        self.gg.set_token(self._privatekey)
        self.gg.set_default_private(self.default_create_private)
        self.gg.setup_session(
                self.session_certificate or not self.session_insecure,
                self.session_proxy)

    def connect(self):
        try:
            self.username = self.user  # Call to self.gg.authenticated_user()
        except HTTPError as err:
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

    @classmethod
    def get_auth_token(cls, login, password, prompt=None):
        import platform
        name = 'git-repo token used on {}'.format(platform.node())
        gg = GogsApi(cls.build_url())
        auth = UsernamePassword(login, password)
        tokens = gg.get_tokens(auth, login)
        tokens = dict((token.name, token.token) for token in tokens)
        if name in tokens:
            return tokens[name]
        if 'git-repo token' in tokens:
            return tokens['git-repo token']
        token = gg.create_token(auth, name, login)
        return token.token

    @property
    def user(self):
        return self.gg.username

    def create(self, user, repo, add=False):
        try:
            self.gg.create_repository(user, repo)
        except ApiFailure as err:
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
            self.gg.delete_repository(user, repo)
        except ApiFailure as err:
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

        repositories = self.gg.repositories(user)
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
            return self.gg.repository(user, repo)
        except ApiFailure as err:
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
