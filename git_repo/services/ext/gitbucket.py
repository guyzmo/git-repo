#!/usr/bin/env python

import logging
log = logging.getLogger('git_repo.gitbucket')

from ..service import register_target
from .github import GithubService

import github3

@register_target('bucket', 'gitbucket')
class GitbucketService(GithubService):
    fqdn = "localhost"
    port = 8080
    def __init__(self, *args, **kwarg):
        super(GitbucketService, self).__init__(*args, **kwarg)

    def connect(self):
        self.gh = github3.GitHubEnterprise(self.build_url(self))
        super(GitbucketService, self).connect()

    @classmethod
    def get_auth_token(cls, login, password, prompt=None):
        print("Please edit _YOUR_ACCESS_TOKEN_ to actual token in ~/.gitconfig or ~/.git/config after.")
        print("And add ssh-url = ssh://git@{}:_YOUR_SSH_PORT_".format(cls.fqdn))
        return "_YOUR_ACCESS_TOKEN_"
        ## this code maybe works when GitBucket supports add access token API.
        #print("build_url: ", cls.build_url(cls))
        #import platform
        #gh = github3.GitHubEnterprise(cls.build_url(cls))
        #gh.login(login, password, two_factor_callback=lambda: prompt('2FA code> '))
        #try:
        #    auth = gh.authorize(login, password,
        #            scopes=[ 'repo', 'delete_repo', 'gist' ],
        #            note='git-repo2 token used on {}'.format(platform.node()),
        #            note_url='https://github.com/guyzmo/git-repo')
        #    return auth.token
        #except github3.models.GitHubError as err:
        #    if len(err.args) > 0 and 422 == err.args[0].status_code:
        #        raise ResourceExistsError("A token already exist for this machine on your github account.")
        #    else:
        #        raise err

    def format_path(self, repository, namespace=None, rw=False):
        path = super(GitbucketService, self).format_path(repository, namespace, rw)
        if not path.endswith(".git"):
            path = "{}.git".format(path)
        return path

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
