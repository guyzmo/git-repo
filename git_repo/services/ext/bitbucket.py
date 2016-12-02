#!/usr/bin/env python

import logging
log = logging.getLogger('git_repo.bitbucket')

from ..service import register_target, RepositoryService
from ...exceptions import ResourceError, ResourceExistsError, ResourceNotFoundError

from pybitbucket.bitbucket import Client, Bitbucket
from pybitbucket.auth import BasicAuthenticator
from pybitbucket.repository import Repository, RepositoryForkPolicy

from requests import Request, Session
from requests.exceptions import HTTPError
import json


@register_target('bb', 'bitbucket')
class BitbucketService(RepositoryService):
    fqdn = 'bitbucket.org'

    def __init__(self, *args, **kwarg):
        self.bb_client = Client()
        self.bb = Bitbucket(self.bb_client)
        super(BitbucketService, self).__init__(*args, **kwarg)

    def connect(self):
        if not self._privatekey:
            raise ConnectionError('Could not connect to BitBucket. Please configure .gitconfig with your bitbucket credentials.')
        if not ':' in self._privatekey:
            raise ConnectionError('Could not connect to BitBucket. Please setup your private key with login:password')
        self.bb_client.config = BasicAuthenticator(*self._privatekey.split(':')+['z+git-repo+pub@m0g.net'])
        self.bb_client.session = self.bb_client.config.session
        try:
            self.user
        except ResourceError as err:
            raise ConnectionError('Could not connect to BitBucket. Not authorized, wrong credentials.') from err

    def create(self, user, repo, add=False):
        try:
            repo = Repository.create(
                    repo,
                    fork_policy=RepositoryForkPolicy.ALLOW_FORKS,
                    is_private=False,
                    client=self.bb_client
            )
            if add:
                self.add(user=user, repo=repo, tracking=self.name)
        except HTTPError as err:
            if '400' in err.args[0].split(' '):
                raise ResourceExistsError('Project {} already exists on this account.'.format(repo)) from err
            raise ResourceError("Couldn't complete creation: {}".format(err)) from err

    def fork(self, user, repo):
        raise NotImplementedError('No support yet by the underlying library.')
        try:
            self.get_repository(user, repo).fork()
        except HTTPError as err:
            raise ResourceError("Couldn't complete fork: {}".format(err)) from err
        return '/'.join([result['owner'], result['slug']])

    def delete(self, repo, user=None):
        if not user:
            user = self.user
        try:
            self.get_repository(user, repo).delete()
        except HTTPError as err:
            if '404' in err.args[0].split(' '):
                raise ResourceNotFoundError("Cannot delete: repository {}/{} does not exists.".format(user, repo)) from err
            raise ResourceError("Couldn't complete deletion: {}".format(err)) from err

    def get_repository(self, user, repo):
        try:
            return next(self.bb.repositoryByOwnerAndRepositoryName(owner=user, repository_name=repo))
        except HTTPError as err:
            raise ResourceNotFoundError('Cannot retrieve repository: {}/{} does not exists.'.format(user, repo))

    @classmethod
    def get_auth_token(cls, login, password, prompt=None):
        log.warn("/!\\ Due to API limitations, the bitbucket login/password is stored as plaintext in configuration.")
        return "{}:{}".format(login, password)

    @property
    def user(self):
        try:
            user = next(self.bb.userForMyself()).username
            return user
        except (HTTPError, AttributeError) as err:
            raise ResourceError("Couldn't find the current user: {}".format(err)) from err


