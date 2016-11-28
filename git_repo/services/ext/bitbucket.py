#!/usr/bin/env python

import logging
log = logging.getLogger('git_repo.bitbucket')

from ..service import register_target, RepositoryService
from ...exceptions import ResourceError, ResourceExistsError, ResourceNotFoundError

from pybitbucket.bitbucket import Client
from pybitbucket.auth import BasicAuthenticator
from pybitbucket.user import User
from pybitbucket.repository import Repository, RepositoryForkPolicy

from requests import Request, Session
from requests.exceptions import HTTPError
import json

# bitbucket.URLS.update({
#     'GET_REPO' : 'repositories/%(username)s/%(repo_slug)s/',
#     'DELETE_REPO' : 'repositories/%(accountname)s/%(repo_slug)s',
#     'FORK_REPO' : 'repositories/%(username)s/%(repo_slug)s/fork',
# })


@register_target('bb', 'bitbucket')
class BitbucketService(RepositoryService):
    fqdn = 'bitbucket.org'

    def __init__(self, *args, **kwarg):
        self.bb = Client()
        super(BitbucketService, self).__init__(*args, **kwarg)

    def connect(self):
        if not self._privatekey:
            raise ConnectionError('Could not connect to BitBucket. Please configure .gitconfig with your bitbucket credentials.')
        if not ':' in self._privatekey:
            raise ConnectionError('Could not connect to BitBucket. Please setup your private key with login:password')
        self.bb.config = BasicAuthenticator(*self._privatekey.split(':')+['z+git-repo+pub@m0g.net'])
        self.bb.session = self.bb.config.session
        try:
            User.find_current_user(client=self.bb)
        except HTTPError as err:
            raise ConnectionError('Could not connect to BitBucket. Not authorized, wrong credentials.') from err

    def create(self, user, repo, add=False):
        try:
            repo = Repository.create(
                    repo,
                    fork_policy=RepositoryForkPolicy.ALLOW_FORKS,
                    is_private=False,
                    client=self.bb
            )
            if add:
                self.add(user=user, repo=repo, tracking=self.name)
        except HTTPError as err:
            if err.status_code == 400:
                raise ResourceExistsError('Project {} already exists on this account.'.format(repo)) from err
            raise ResourceError("Couldn't complete creation: {}".format(err)) from err

    def fork(self, user, repo):
        raise NotImplementedError('No support yet by the underlying library.')
        try:
            Repository.find_repository_by_name_and_owner(repo, owner=user, client=self.bb).fork()
        except HTTPError as err:
            raise ResourceError("Couldn't complete creation: {}".format(err)) from err
        return '/'.join([result['owner'], result['slug']])

    def delete(self, repo, user=None):
        if not user:
            user = self.user
        try:
            Repository.find_repository_by_name_and_owner(repo, owner=user, client=self.bb).delete()
        except HTTPError as err:
            if err.status_code == 404:
                raise ResourceNotFoundError("Cannot delete: repository {}/{} does not exists.".format(user, repo)) from err
            raise ResourceError("Couldn't complete creation: {}".format(err)) from err

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

        try:
            user = User.find_user_by_username(user)
        except HTTPError as err:
            raise ResourceNotFoundError("User {} does not exists.".format(user)) from err

        repositories = user.repositories()
        if not _long:
            repositories = list(repositories)
            col_print(["/".join([user.username, repo.name]) for repo in repositories])
        else:
            print('Status\tCommits\tReqs\tIssues\tForks\tCoders\tWatch\tLikes\tLang\tModif\t\tName', file=sys.stderr)
            for repo in repositories:
                # if repo.updated_at.year < datetime.now().year:
                #     date_fmt = "%b %d %Y"
                # else:
                #     date_fmt = "%b %d %H:%M"

                status = ''.join([
                    'F' if getattr(repo, 'parent', None) else ' ',               # is a fork?
                    'P' if repo.is_private else ' ',            # is private?
                ])
                print('\t'.join([
                    # status
                    status,
                    # stats
                    str(len(list(repo.commits()))),          # number of commits
                    str(len(list(repo.pullrequests()))),            # number of pulls
                    str('N.A.'),           # number of issues
                    str(len(list(repo.forks()))),                              # number of forks
                    str('N.A.'),     # number of contributors
                    str(len(list(repo.watchers()))),                           # number of subscribers
                    str('N.A.'),                    # number of ♥
                    # info
                    repo.language or '?',                      # language
                    repo.updated_on,      # date
                    '/'.join([user.username, repo.name]),             # name
                ]))

    def get_repository(self, user, repo):
        try:
            return Repository.find_repository_by_name_and_owner(repo, owner=user, client=self.bb)
        except HTTPError as err:
            raise ResourceNotFoundError('Cannot retrieve repository: {}/{} does not exists.'.format(user, repo))

    @classmethod
    def get_auth_token(cls, login, password, prompt=None):
        log.warn("/!\\ Due to API limitations, the bitbucket login/password is stored as plaintext in configuration.")
        return "{}:{}".format(login, password)

    @property
    def user(self):
        try:
            return User.find_current_user(client=self.bb).username
        except HTTPError as err:
            raise ResourceError("Couldn't complete creation: {}".format(err)) from err


