#!/usr/bin/env python3

import logging
log = logging.getLogger('git_repo.gitbucket')

from ..service import register_target
from .github import GithubService
from ...exceptions import ArgumentError

import github3

@register_target('bucket', 'gitbucket')
class GitbucketService(GithubService):
    fqdn = "localhost"
    port = 8080

    def __init__(self, *args, **kwarg):
        super(GitbucketService, self).__init__(*args, **kwarg)

    @classmethod
    def get_auth_token(cls, login, password, prompt=None):
        print("Please open the following URL: {}/{}/_application".format(cls.build_url(cls), login))
        print("Generate a new token, and paste it at the following prompt.")
        return prompt('token> ')

    def format_path(self, repository, namespace=None, rw=False):
        repo = repository
        if namespace:
            repo = '{}/{}'.format(namespace, repository)

        if not rw and '/' in repo:
            return '{}/git/{}.git'.format(self.url_ro, repo)
        elif rw and '/' in repo:
            if 'ssh://' in self.url_rw:
                return '{}/{}.git'.format(self.url_rw, repo)
            else:
                return '{}:{}.git'.format(self.url_rw, repo)
        else:
            raise ArgumentError("Cannot tell how to handle this url: `{}/{}`!".format(namespace, repo))

    def delete(self, repo, user=None):
        raise NotImplementedError("GitBucket doesn't suport this action now.")

    def request_create(self, user, repo, from_branch, onto_branch, title=None, description=None, auto_slug=False, edit=None):
        raise NotImplementedError("GitBucket doesn't support this action now.")

    def gist_list(self, gist=None):
        raise NotImplementedError("GitBucket doesn't support manipulate gist by API.")

    def gist_fetch(self, gist, fname=None):
        raise NotImplementedError("GitBucket doesn't support manipulate gist by API.")

    def gist_clone(self, gist):
        raise NotImplementedError("GitBucket doesn't support manipulate gist by API.")

    def gist_create(self, gist_pathes, description, secret=False):
        raise NotImplementedError("GitBucket doesn't support manipulate gist by API.")

    def gist_delete(self, gist_id):
        raise NotImplementedError("GitBucket doesn't support manipulate gist by API.")
