#!/usr/bin/env python
import sys
import logging
log = logging.getLogger('git_repo.gogs')

from ..service import register_target, RepositoryService, os
from ...exceptions import ResourceError, ResourceExistsError, ResourceNotFoundError
from ...tools import columnize

from gogs_client import GogsApi, GogsRepo, Token, UsernamePassword, ApiFailure
from requests import Session, HTTPError
from urllib.parse import urlparse, urlunparse
from datetime import datetime
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
        # this is required to detect fresh GoGS server that redirects everything to /install
        self.session.max_redirects = 0

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

    def connect(self):
        self.gg.setup(self.url_ro)
        self.gg.set_token(self._privatekey)
        self.gg.set_default_private(self.default_create_private)
        self.gg.setup_session(
                self.session_certificate or not self.session_insecure,
                self.session_proxy)
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
        gg = GogsApi(cls.build_url(cls))
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

        repositories = self.gg.repositories(user)
        if user != self.username and not repositories and user not in self.orgs:
            raise ResourceNotFoundError("Unable to list namespace {} - only authenticated user and orgs available for listing.".format(user))
        if not _long:
            repositories = list([repo['full_name'] for repo in repositories])
            yield "{}"
            yield "Total repositories: {}".format(len(repositories))
            yield from columnize(repositories)
        else:
            yield ['Status', 'Commits', 'Reqs', 'Issues', 'Forks', 'Coders', 'Watch', 'Likes', 'Lang', 'Modif\t', 'Name']
            for repo in repositories:
                status = ''.join([
                    'F' if repo['fork'] else ' ',          # is a fork?
                    'P' if repo['private'] else ' ',       # is private?
                ])
                try:
                    issues = self.gg._check_ok(self.gg._get('/repos/{}/issues'.format(repo['full_name']), auth=self.auth)).json()
                except Exception:
                    issues = []
                yield [
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
                ]

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
