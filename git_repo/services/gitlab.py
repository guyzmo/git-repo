#!/usr/bin/env python

import logging
log = logging.getLogger('git_repo.gitlab')

import json

from .base import register_target, RepositoryService

from gitlab import Gitlab
from gitlab.exceptions import GitlabCreateError, GitlabGetError

@register_target('lab', 'gitlab')
class GitlabService(RepositoryService):
    fqdn = 'gitlab.com'

    def connect(self):
        self.gl = Gitlab(self.url_ro, self._privatekey)

    def create(self, repo):
        repo_name = repo
        if '/' in repo:
            user, repo_name = repo.split('/')
        try:
            self.gl.projects.create(data={
                'name': repo_name,
                # 'namespace_id': user, # TODO does not work, cannot create on
                # another namespace yet
            })
        except GitlabCreateError as err:
            if json.loads(err.response_body.decode('utf-8'))['message']['name'][0] == 'has already been taken':
                raise Exception("Project already exists.")
            else:
                raise Exception("Unhandled error.")
        self.add(user=user, repo=repo_name, default=True)

    def fork(self, user, repo, branch='master'):
        try:
            fork = self.gl.projects.get('{}/{}'.format(user, repo)).forks.create({})
        except GitlabCreateError as err:
            if json.loads(err.response_body.decode('utf-8'))['message']['name'][0] == 'has already been taken':
                raise Exception("Project already exists.")
            else:
                raise Exception("Unhandled error.")
        self.add(user=user, repo=repo, name='upstream', alone=True)
        remote = self.add(repo=fork.name, user=fork.namespace['path'], default=True)
        self.pull(remote, branch)
        log.info("New forked repository available at {}/{}".format(self.url_ro,
                                                                   fork.path_with_namespace))

    def delete(self, repo_name, user=None):
        if not user:
            raise Exception('Need an user namespace')
        try:
            repo = self.gl.projects.get('{}/{}'.format(user, repo_name))
            if repo:
                result = repo.delete()
            if not repo or not result:
                raise Exception("Cannot delete: repository {}/{} does not exists.".format(user, repo_name))
        except GitlabGetError as err:
            if err.response_code == 404:
                raise Exception("Cannot delete: repository {}/{} does not exists.".format(user, repo_name))
            elif err.response_code == 403:
                raise Exception("You don't have enough permissions for deleting the repository. Check the namespace or the private token's privileges")
        except Exception as err:
            raise Exception("Unhandled exception: {}".format(err))


