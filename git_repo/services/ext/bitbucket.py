#!/usr/bin/env python

import logging
log = logging.getLogger('git_repo.bitbucket')

from ..service import register_target, RepositoryService
from ...exceptions import ResourceError, ResourceExistsError, ResourceNotFoundError

from pybitbucket.bitbucket import Client, Bitbucket
from pybitbucket.auth import BasicAuthenticator
from pybitbucket.repository import Repository, RepositoryForkPolicy
from pybitbucket.snippet import Snippet

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

    def _format_gist(self, gist):
        return gist.split('/')[-1] if gist.startswith('http') else gist

    def gist_list(self, gist=None):
        if not gist:
            for snippet in list(self.bb.snippetByOwner(owner=self.user)):
                if isinstance(snippet, Snippet):
                    yield (snippet.links['html']['href'], snippet.title)
        else:
            try:
                snippet = next(self.bb.snippetByOwnerAndSnippetId(owner=self.user, snippet_id=self._format_gist(gist)))
                for snippet_file in snippet.filenames:
                    yield ('N.A.',
                            0,
                            snippet_file)
            except HTTPError as err:
                if '404' in err.args[0].split(' '):
                    raise ResourceNotFoundError("Could not find snippet {}.".format(gist)) from err
                raise ResourceError("Couldn't fetch snippet details: {}".format(err)) from err

    def gist_fetch(self, gist, fname=None):
        gist = self._format_gist(gist)
        try:
            user = self.user
            snippet = next(self.bb.snippetByOwnerAndSnippetId(owner=user, snippet_id=gist))
        except HTTPError as err:
            if '404' in err.args[0].split(' '):
                raise ResourceNotFoundError("Could not find snippet {}.".format(gist)) from err
            raise ResourceError("Couldn't fetch snippet details: {}".format(err)) from err
        if len(snippet.filenames) == 1 and not fname:
            gist_file = snippet.filenames[0]
        else:
            if fname in snippet.filenames:
                gist_file = fname
            else:
                raise ResourceNotFoundError('Could not find file within gist.')

        return self.bb_client.session.get(
                    'https://bitbucket.org/!api/2.0/snippets/{}/{}/files/{}'.format(user, gist, gist_file)
                ).content.decode('utf-8')

    def gist_clone(self, gist):
        gist = self._format_gist(gist)
        try:
            snippet = next(self.bb.snippetByOwnerAndSnippetId(owner=self.user, snippet_id=gist))
            remotes = {it['name']: it['href'] for it in snippet.links['clone']}
            if 'ssh' in remotes:
                remote = remotes['ssh']
            elif 'ssh' in remotes:
                remote = remotes['https']
            else:
                raise ResourceError("Couldn't find appropriate method for cloning.")
        except HTTPError as err:
            if '404' in err.args[0].split(' '):
                raise ResourceNotFoundError("Could not find snippet {}.".format(gist)) from err
            raise ResourceError("Couldn't fetch snippet details: {}".format(err)) from err
        remote = self.repository.create_remote('gist', remote)
        self.pull(remote, 'master')

    def gist_create(self, gist_pathes, description, secret=False):
        def load_file(fname, path='.'):
            with open(os.path.join(path, fname), 'r') as f:
                return {'content': f.read()}

        gist_files = dict()
        for gist_path in gist_pathes:
            if not os.path.isdir(gist_path):
                gist_files[os.path.basename(gist_path)] = load_file(gist_path)
            else:
                for gist_file in os.listdir(gist_path):
                    if not os.path.isdir(os.path.join(gist_path, gist_file)) and not gist_file.startswith('.'):
                        gist_files[gist_file] = load_file(gist_file, gist_path)

        gist = self.gh.create_gist(
                description=description,
                files=gist_files,
                public=not secret # isn't it obvious? ☺
            )

        return gist.html_url

    def gist_delete(self, gist_id):
        gist = self.gh.gist(self._format_gist(gist_id))
        if not gist:
            raise ResourceNotFoundError('Could not find gist')
        gist.delete()

    def request_create(self, user, repo, local_branch, remote_branch, title, description=None):
        repository = self.gh.repository(user, repo)
        if not repository:
            raise ResourceNotFoundError('Could not find repository `{}/{}`!'.format(user, repo))
        if not remote_branch:
            remote_branch =  self.repository.active_branch.name
        if not local_branch:
            local_branch = repository.master_branch or 'master'
        try:
            request = repository.create_pull(title,
                    base=local_branch,
                    head=':'.join([user, remote_branch]),
                    body=description)
        except github3.models.GitHubError as err:
            if err.code == 422:
                if err.message == 'Validation Failed':
                    for error in err.errors:
                        if 'message' in error:
                            raise ResourceError(error['message'])
                    raise ResourceError("Unhandled formatting error: {}".format(err.errors))
            raise ResourceError(err.message)

        return {'local': local_branch, 'remote': remote_branch, 'ref': request.number}

    def request_list(self, user, repo):
        repository = self.gh.repository(user, repo)
        for pull in repository.iter_pulls():
            yield ( str(pull.number), pull.title, pull.links['issue'] )

    def request_fetch(self, user, repo, request, pull=False):
        if pull:
            raise NotImplementedError('Pull operation on requests for merge are not yet supported')
        try:
            for remote in self.repository.remotes:
                if remote.name == self.name:
                    local_branch_name = 'request/{}'.format(request)
                    self.fetch(
                        remote,
                        'pull/{}/head'.format(request),
                        local_branch_name
                    )
                    return local_branch_name
            else:
                raise ResourceNotFoundError('Could not find remote {}'.format(self.name))
        except GitCommandError as err:
            if 'Error when fetching: fatal: Couldn\'t find remote ref' in err.command[0]:
                raise ResourceNotFoundError('Could not find opened request #{}'.format(request)) from err
            raise err

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


