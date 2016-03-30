#!/usr/bin/env python

import logging
log = logging.getLogger('git_repo.gitlab')

from ..service import register_target, RepositoryService
from ...exceptions import ArgumentError, ResourceError, ResourceExistsError, ResourceNotFoundError

import gitlab
from gitlab.exceptions import GitlabCreateError, GitlabGetError

import json

@register_target('lab', 'gitlab')
class GitlabService(RepositoryService):
    fqdn = 'gitlab.com'

    def __init__(self, *args, **kwarg):
        self.gl = gitlab.Gitlab(self.url_ro)
        super(GitlabService, self).__init__(*args, **kwarg)

    def connect(self):
        self.gl.set_token(self._privatekey)
        self.gl.token_auth()

    def create(self, user, repo, add=False):
        try:
            self.gl.projects.create(data={
                'name': repo,
                # 'namespace_id': user, # TODO does not work, cannot create on
                # another namespace yet
            })
        except GitlabCreateError as err:
            if json.loads(err.response_body.decode('utf-8'))['message']['name'][0] == 'has already been taken':
                raise ResourceExistsError("Project already exists.") from err
            else:
                raise ResourceError("Unhandled error.") from err
        if add:
            self.add(user=user, repo=repo, tracking=self.name)

    def fork(self, user, repo, branch='master', clone=False):
        try:
            fork = self.gl.projects.get('{}/{}'.format(user, repo)).forks.create({})
        except GitlabCreateError as err:
            if json.loads(err.response_body.decode('utf-8'))['message']['name'][0] == 'has already been taken':
                raise ResourceExistsError("Project already exists.") from err
            else:
                raise ResourceError("Unhandled error: {}".format(err)) from err
        self.add(user=user, repo=repo, name='upstream', alone=True)
        remote = self.add(repo=fork.path, user=fork.namespace['path'], tracking=self.name)
        if clone:
            self.pull(remote, branch)
        log.info("New forked repository available at {}/{}".format(self.url_ro,
                                                                   fork.path_with_namespace))

    def delete(self, repo, user=None):
        if not user:
            user = self.user
        try:
            repository = self.gl.projects.get('{}/{}'.format(user, repo))
            if repository:
                result = self.gl.delete(repository.__class__, repository.id)
            if not repository or not result:
                raise ResourceNotFoundError("Cannot delete: repository {}/{} does not exists.".format(user, repo))
        except GitlabGetError as err:
            if err.response_code == 404:
                raise ResourceNotFoundError("Cannot delete: repository {}/{} does not exists.".format(user, repo)) from err
            elif err.response_code == 403:
                raise ResourcePermissionError("You don't have enough permissions for deleting the repository. Check the namespace or the private token's privileges") from err
        except Exception as err:
            raise ResourceError("Unhandled exception: {}".format(err)) from err

    def get_repository(self, user, repo):
        try:
            return self.gl.projects.get('{}/{}'.format(user, repo))
        except GitlabGetError as err:
            if err.response_code == 404:
                raise ResourceNotFoundError("Cannot delete: repository {}/{} does not exists.".format(user, repo)) from err

    @property
    def user(self):
        return self.gl.user.username

