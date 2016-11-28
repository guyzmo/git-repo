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


