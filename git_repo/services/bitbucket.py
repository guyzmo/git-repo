#!/usr/bin/env python

import logging
log = logging.getLogger('git_repo.bitbucket')

from .base import register_target, RepositoryService

from bitbucket.bitbucket import Bitbucket
import json


def monkey_patch(bb):
    import types
    # XXX odious monkey patching, need to do a PR upstream on bitbucket-api
    # def get(self, user=None, repo_slug=None):
    #     """ Get a single repository on Bitbucket and return it."""
    #     username = user or self.bitbucket.username
    #     repo_slug = repo_slug or self.bitbucket.repo_slug or ''
    #     url = self.bitbucket.url('GET_REPO', username=username, repo_slug=repo_slug)
    #     return self.bitbucket.dispatch('GET', url, auth=self.bitbucket.auth)
    #
    # bb.repository.bitbucket.URLS['GET_REPO'] = 'repositories/%(username)s/%(repo_slug)s/'
    # bb.repository.get_repo = types.MethodType(get, bb.repository)

    def delete(self, user, repo_slug):
        url = self.bitbucket.url('DELETE_REPO', accountname=user, repo_slug=repo_slug)
        return self.bitbucket.dispatch('DELETE', url, auth=self.bitbucket.auth)

    bb.repository.bitbucket.URLS['DELETE_REPO'] = 'repositories/%(accountname)s/%(repo_slug)s'
    bb.repository.delete = types.MethodType(delete, bb.repository)

    def fork(self, user, repo_slug, new_name=None):
        url = self.bitbucket.url('FORK_REPO', username=user, repo_slug=repo_slug)
        new_repo = new_name or repo_slug
        return self.bitbucket.dispatch('POST', url, name=new_repo, auth=self.bitbucket.auth)

    bb.repository.bitbucket.URLS['FORK_REPO'] = 'repositories/%(username)s/%(repo_slug)s/fork'
    bb.repository.fork = types.MethodType(fork, bb.repository)

    from requests import Request, Session
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
        s = Session()
        resp = s.send(r.prepare())
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

    bb.repository.bitbucket.dispatch = types.MethodType(dispatch, bb.repository.bitbucket)


@register_target('bb', 'bitbucket')
class BitbucketService(RepositoryService):
    fqdn = 'bitbucket.org'

    def connect(self):
        username, password = self._privatekey.split(':')
        self.bb = Bitbucket(username, password)
        monkey_patch(self.bb)

    def create(self, repo):
        repo_name = repo
        if '/' in repo:
            user, repo_name = repo.split('/')
        try:
            self.bb.repository.create(repo_name, scm='git')
        except Exception as err:
            if err.message == 'name already exists on this account':
                raise Exception("Project already exists.")
            else:
                raise Exception("Unhandled error.")
        self.add(user=user, repo=repo_name, default=True)

    def fork(self, user, repo, branch='master'):
        log.info("Forking repository {}/{}…".format(user, repo))
        success, result = self.bb.repository.fork(user, repo)
        if not success:
            raise Exception("Couldn't complete fork: {message} (error #{code}: {reason})".format(**result))
        fork = result
        self.add(repo=repo, user=user, name='upstream', alone=True)
        remote = self.add(repo=fork['slug'], user=fork['owner'], default=True)
        self.pull(remote, branch)
        log.info("New forked repository available at {}".format(self.format_path(fork['slug'], fork['owner'])))

    def delete(self, repo, user=None):
        if not user:
            user = self.bb.user().name
        success, result = self.bb.repository.delete(user, repo)
        if not success and result['code'] == 404:
            raise Exception("Cannot delete: repository {}/{} does not exists.".format(user, repo))
        elif not success:
            raise Exception("Couldn't complete deletion: {message} (error #{code}: {reason})".format(**result))


