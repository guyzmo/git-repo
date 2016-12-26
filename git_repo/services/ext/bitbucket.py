#!/usr/bin/env python

import logging
log = logging.getLogger('git_repo.bitbucket')

from ..service import register_target, RepositoryService
from ...exceptions import ResourceError, ResourceExistsError, ResourceNotFoundError

from pybitbucket.bitbucket import Client, Bitbucket
from pybitbucket.auth import BasicAuthenticator
from pybitbucket.pullrequest import PullRequest, PullRequestPayload
from pybitbucket.repository import (
        Repository, RepositoryPayload, RepositoryForkPayload,
        RepositoryForkPolicy, RepositoryType
)
from pybitbucket.snippet import Snippet, SnippetPayload
from pybitbucket.user import User

from requests import Request, Session
from requests.exceptions import HTTPError
import os, json


@register_target('bb', 'bitbucket')
class BitbucketService(RepositoryService):
    fqdn = 'bitbucket.org'

    def __init__(self, *args, **kwarg):
        self.bb = Bitbucket(Client())
        super(BitbucketService, self).__init__(*args, **kwarg)

    def connect(self):
        if not self._privatekey:
            raise ConnectionError('Could not connect to BitBucket. Please configure .gitconfig with your bitbucket credentials.')
        if not ':' in self._privatekey:
            raise ConnectionError('Could not connect to BitBucket. Please setup your private key with login:password')
        auth = BasicAuthenticator(*self._privatekey.split(':')+['z+git-repo+pub@m0g.net'])
        self.bb.client.config = auth
        self.bb.client.session = self.bb.client.config.session = auth.start_http_session(self.bb.client.session)
        try:
            _ = self.bb.client.config.who_am_i()
        except ResourceError as err:
            raise ConnectionError('Could not connect to BitBucket. Not authorized, wrong credentials.') from err

    def create(self, user, repo, add=False):
        try:
            repo = Repository.create(
                    RepositoryPayload(dict(
                        fork_policy=RepositoryForkPolicy.ALLOW_FORKS,
                        is_private=False
                    )),
                    repository_name=repo,
                    owner=user,
                    client=self.bb.client
            )
            if add:
                self.add(user=user, repo=repo.name, tracking=self.name)
        except HTTPError as err:
            if '400' in err.args[0].split(' '):
                raise ResourceExistsError('Project {} already exists on this account.'.format(repo)) from err
            raise ResourceError("Couldn't complete creation: {}".format(err)) from err

    def fork(self, user, repo):
        # result = self.get_repository(user, repo).fork(
        #     RepositoryForkPayload(dict(name=repo)),
        #     owner=user)
        resp = self.bb.client.session.post(
            'https://api.bitbucket.org/1.0/repositories/{}/{}/fork'.format(user, repo),
            data={'name': repo}
        )
        if 404 == resp.status_code:
            raise ResourceNotFoundError("Couldn't complete fork: {}".format(resp.content.decode('utf-8')))
        elif 200 != resp.status_code:
            raise ResourceError("Couldn't complete fork: {}".format(resp.content.decode('utf-8')))
        result = resp.json()
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

        return self.bb.client.session.get(
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
            return open(os.path.join(path, fname), 'r')

        gist_files = dict()
        for gist_path in gist_pathes:
            if not os.path.isdir(gist_path):
                gist_files[os.path.basename(gist_path)] = load_file(gist_path)
            else:
                for gist_file in os.listdir(gist_path):
                    if not os.path.isdir(os.path.join(gist_path, gist_file)) and not gist_file.startswith('.'):
                        gist_files[gist_file] = load_file(gist_file, gist_path)

        try:
            snippet = Snippet.create(
                files=gist_files,
                payload=SnippetPayload(
                    payload=dict(
                        title=description,
                        scm=RepositoryType.GIT,
                        is_private=secret
                    )
                ),
                client=self.bb.client
            )

            return snippet.links['html']['href']
        except HTTPError as err:
            raise ResourceError("Couldn't create snippet: {}".format(err)) from err

    def gist_delete(self, gist_id):
        try:
            snippet = next(self.bb.snippetByOwnerAndSnippetId(owner=self.user, snippet_id=gist_id)).delete()
        except HTTPError as err:
            if '404' in err.args[0].split(' '):
                raise ResourceNotFoundError("Could not find snippet {}.".format(gist_id)) from err
            raise ResourceError("Couldn't delete snippet: {}".format(err)) from err

    def request_create(self, user, repo, local_branch, remote_branch, title, description=None):
        try:
            repository = next(self.bb.repositoryByOwnerAndRepositoryName(owner=user, repository_name=repo))
            if not repository:
                raise ResourceNotFoundError('Could not find repository `{}/{}`!'.format(user, repo))
            if not remote_branch:
                try:
                    remote_branch = next(repository.branches()).name
                except StopIteration:
                    remote_branch = 'master'
            if not local_branch:
                local_branch = self.repository.active_branch.name
            request = PullRequest.create(
                        PullRequestPayload(
                            payload=dict(
                                title=title,
                                description=description or '',
                                destination=dict(
                                    branch=dict(name=remote_branch)
                                ),
                                source=dict(
                                    repository=dict(full_name='/'.join([self.user, repo])),
                                    branch=dict(name=local_branch)
                                )
                            )
                        ),
                        repository_name=repo,
                        owner=user,
                        client=self.bb.client
                    )
        except HTTPError as err:
            status_code = hasattr(err, 'code') and err.code or err.response.status_code
            if 404 == status_code:
                raise ResourceNotFoundError("Couldn't create request, project not found: {}".format(repo)) from err
            elif 400 == status_code and 'branch not found' in err.format_message():
                raise ResourceNotFoundError("Couldn't create request, branch not found: {}".format(local_branch)) from err
            raise ResourceError("Couldn't create request: {}".format(err)) from err

        return {'local': local_branch, 'remote': remote_branch, 'ref': str(request.id)}

    def request_list(self, user, repo):
        requests = set(
            (
                str(r.id),
                r.title,
                r.links['html']['href']
            ) for r in self.bb.repositoryPullRequestsInState(
                owner=user,
                repository_name=repo,
                state='open'
            ) if not isinstance(r, dict) # if no PR is empty, result is a dict
        )
        for pull in sorted(requests):
            try:
                yield pull
            except Exception as err:
                log.warn('Error while fetching request information: {}'.format(pull))

    def request_fetch(self, user, repo, request, pull=False):
        log.warn('Bitbucket does not support fetching of PR using git. Use this command at your own risk.')
        if 'y' not in input('Are you sure to continue? [yN]> '):
            raise ResourceError('Command aborted.')
        if pull:
            raise NotImplementedError('Pull operation on requests for merge are not yet supported')
        try:
            repository = self.get_repository(user, repo)
            if self.repository.is_dirty():
                raise ResourceError('Please use this command after stashing your changes.')
            local_branch_name = 'requests/bitbucket/{}'.format(request)
            index = self.repository.index
            log.info('» Fetching pull request {}'.format(request))
            request = next(bb.repositoryPullRequestByPullRequestId(
                owner=user,
                repository_name=repo,
                pullrequest_id=request
            ))
            commit = self.repository.rev_parse(request['destination']['commit']['hash'])
            self.repository.head.reference = commit
            log.info('» Creation of requests branch {}'.format(local_branch_name))
            # create new branch
            head = self.repository.create_head(local_branch_name)
            head.checkout()
            # fetch and apply patch
            log.info('» Fetching and writing the patch in current directory')
            patch = bb.client.session.get(request['links']['diff']['href']).content.decode('utf-8')
            with open('.tmp.patch', 'w') as f:
                f.write(patch)
            log.info('» Applying the patch')
            git.cmd.Git().apply('.tmp.patch', stat=True)
            os.unlink('.tmp.patch')
            log.info('» Going back to original branch')
            index.checkout() # back to former branch
            return local_branch_name
        except HTTPError as err:
            if '404' in err.args[0].split(' '):
                raise ResourceNotFoundError("Could not find snippet {}.".format(gist_id)) from err
            raise ResourceError("Couldn't delete snippet: {}".format(err)) from err
        except GitCommandError as err:
            if 'Error when fetching: fatal: ' in err.command[0]:
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


