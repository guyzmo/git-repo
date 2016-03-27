#!/usr/bin/env python

import logging
log = logging.getLogger('git_repo.bitbucket')

from ..service import register_target, RepositoryService
from ...exceptions import ResourceError, ResourceExistsError, ResourceNotFoundError

import bitbucket.bitbucket as bitbucket
from requests import Request, Session
import json

'''
Extension of the bitbucket module implementation to add support for the extra
features the original implementation lacked. This is a temporary measure, up
until a PR is crafted for the original code.
'''

bitbucket.URLS.update({
    'GET_REPO' : 'repositories/%(username)s/%(repo_slug)s/',
    'DELETE_REPO' : 'repositories/%(accountname)s/%(repo_slug)s',
    'FORK_REPO' : 'repositories/%(username)s/%(repo_slug)s/fork',
})

class Bitbucket(bitbucket.Bitbucket):
    def __init__(self, *args, **kwarg):
        super(Bitbucket, self).__init__(self)
        self.session = Session()
        # XXX monkey patching of requests within bitbucket module
        bitbucket.requests = self.session

    def get(self, user=None, repo_slug=None):
        """ Get a single repository on Bitbucket and return it."""
        username = user or self.bitbucket.username
        repo_slug = repo_slug or self.bitbucket.repo_slug or ''
        url = self.bitbucket.url('GET_REPO', username=username, repo_slug=repo_slug)
        return self.bitbucket.dispatch('GET', url, auth=self.bitbucket.auth)

    def delete(self, user, repo_slug):
        url = self.bitbucket.url('DELETE_REPO', accountname=user, repo_slug=repo_slug)
        return self.bitbucket.dispatch('DELETE', url, auth=self.bitbucket.auth)

    def fork(self, user, repo_slug, new_name=None):
        url = self.bitbucket.url('FORK_REPO', username=user, repo_slug=repo_slug)
        new_repo = new_name or repo_slug
        return self.bitbucket.dispatch('POST', url, name=new_repo, auth=self.bitbucket.auth)

    def dispatch(self, method, url, auth=None, params=None, **kwargs):
        """ Send HTTP request, with given method,
            credentials and data to the given URL,
            and return the success and the result on success.
        """
        r = Request(
            method=method,
            url=url,
            auth=auth,
            params=params,
            data=kwargs)
        resp = self.session.send(r.prepare())
        status = resp.status_code
        text = resp.text
        error = resp.reason
        if status >= 200 and status < 300:
            if text:
                try:
                    return (True, json.loads(text))
                except TypeError:
                    pass
                except ValueError:
                    pass
            return (True, text)
        elif status >= 300 and status < 400:
            return (
                False,
                'Unauthorized access, '
                'please check your credentials.')
        elif status == 404:
            return (False, dict(message='Service not found', reason=error, code=status))
        elif status == 400:
            return (False, dict(message='Bad request sent to server.', reason=error, code=status))
        elif status == 401:
            return (False, dict(message='Not enough privileges.', reason=error, code=status))
        elif status == 403:
            return (False, dict(message='Not authorized.', reason=error, code=status))
        elif status == 402 or status >= 405:
            return (False, dict(message='Request error.', reason=error, code=status))
        elif status >= 500 and status < 600:
                return (False, dict(message='Server error.', reason=error, code=status))
        else:
            return (False, dict(message='Unidentified error.', reason=error, code=status))


@register_target('bb', 'bitbucket')
class BitbucketService(RepositoryService):
    fqdn = 'bitbucket.org'

    def __init__(self, *args, **kwarg):
        self.bb = Bitbucket()
        super(BitbucketService, self).__init__(*args, **kwarg)

    def connect(self):
        if not self._privatekey:
            raise ConnectionError('Could not connect to BitBucket. Please configure .gitconfig with your bitbucket credentials.')
        if not ':' in self._privatekey:
            raise ConnectionError('Could not connect to BitBucket. Please setup your private key with login:password')
        self.bb.username, self.bb.password = self._privatekey.split(':')

    def create(self, user, repo):
        success, result = self.bb.repository.create(repo, scm='git')
        if not success and result['code'] == 400:
            raise ResourceExistsError('Project {} already exists on this account.'.format(repo))
        elif not success:
            raise ResourceError("Couldn't complete creation: {message} (error #{code}: {reason})".format(**result))
        self.add(user=user, repo=repo, default=True)

    def fork(self, user, repo, branch='master', clone=True):
        log.info("Forking repository {}/{}…".format(user, repo))
        success, result = self.bb.repository.fork(user, repo)
        if not success:
            raise ResourceError("Couldn't complete fork: {message} (error #{code}: {reason})".format(**result))
        fork = result
        self.add(repo=repo, user=user, name='upstream', alone=True)
        remote = self.add(repo=fork['slug'], user=fork['owner'], default=True)
        if clone:
            self.pull(remote, branch)
        log.info("New forked repository available at {}".format(self.format_path(fork['slug'], fork['owner'])))

    def delete(self, repo, user=None):
        if not user:
            user = self.bb._username
        success, result = self.bb.repository.delete(user, repo)
        if not success and result['code'] == 404:
            raise ResourceNotFoundError("Cannot delete: repository {}/{} does not exists.".format(user, repo))
        elif not success:
            raise ResourceError("Couldn't complete deletion: {message} (error #{code}: {reason})".format(**result))

    @property
    def user(self):
        ret, user = bb.get_user()
        if ret:
            return user['username']
        raise ResourceError("Could not retrieve username: {message} (error #{code}: {reason}".format(**result))


