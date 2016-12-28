#!/usr/bin/env python

import logging
log = logging.getLogger('git_repo.github')

from ..service import register_target, RepositoryService, os
from ...exceptions import ResourceError, ResourceExistsError, ResourceNotFoundError

import github3

from git.exc import GitCommandError

@register_target('hub', 'github')
class GithubService(RepositoryService):
    fqdn = 'github.com'

    def __init__(self, *args, **kwarg):
        self.gh = github3.GitHub()
        super(GithubService, self).__init__(*args, **kwarg)

    def connect(self):
        try:
            self.gh.login(token=self._privatekey)
            self.username = self.gh.user().login
        except github3.models.GitHubError as err:
            if 401 == err.code:
                if not self._privatekey:
                    raise ConnectionError('Could not connect to Github. '
                                          'Please configure .gitconfig '
                                          'with your github private key.') from err
                else:
                    raise ConnectionError('Could not connect to Github. '
                                          'Check your configuration and try again.') from err

    def create(self, user, repo, add=False):
        try:
            if user != self.username:
                org = self.gh.organization(user)
                if org:
                    org.create_repo(repo)
                else:
                    raise ResourceNotFoundError("Namespace {} neither an organization or current user.".format(user))
            else:
                self.gh.create_repo(repo)
        except github3.models.GitHubError as err:
            if err.code == 422 or err.message == 'name already exists on this account':
                raise ResourceExistsError("Project already exists.") from err
            else: # pragma: no cover
                raise ResourceError("Unhandled error.") from err
        if add:
            self.add(user=self.username, repo=repo, tracking=self.name)

    def fork(self, user, repo):
        try:
            return self.gh.repository(user, repo).create_fork().full_name
        except github3.models.GitHubError as err:
            if err.message == 'name already exists on this account':
                raise ResourceExistsError("Project already exists.") from err
            else: # pragma: no cover
                raise ResourceError("Unhandled error: {}".format(err)) from err

    def delete(self, repo, user=None):
        if not user:
            user = self.username
        try:
            repository = self.gh.repository(user, repo)
            if repository:
                result = repository.delete()
            if not repository or not result:
                raise ResourceNotFoundError('Cannot delete: repository {}/{} does not exists.'.format(user, repo))
        except github3.models.GitHubError as err: # pragma: no cover
            if err.code == 403:
                raise ResourcePermissionError('You don\'t have enough permissions for deleting the repository. '
                                              'Check the namespace or the private token\'s privileges') from err
            raise ResourceError('Unhandled exception: {}'.format(err)) from err

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

        if not self.gh.user(user):
            raise ResourceNotFoundError("User {} does not exists.".format(user))

        repositories = self.gh.iter_user_repos(user)
        if not _long:
            repositories = list(repositories)
            col_print(["/".join([user, repo.name]) for repo in repositories])
        else:
            print('Status\tCommits\tReqs\tIssues\tForks\tCoders\tWatch\tLikes\tLang\tModif\t\tName', file=sys.stderr)
            for repo in repositories:
                try:
                    if repo.updated_at.year < datetime.now().year:
                        date_fmt = "%b %d %Y"
                    else:
                        date_fmt = "%b %d %H:%M"

                    status = ''.join([
                        'F' if repo.fork else ' ',               # is a fork?
                        'P' if repo.private else ' ',            # is private?
                    ])
                    print('\t'.join([
                        # status
                        status,
                        # stats
                        str(len(list(repo.iter_commits()))),          # number of commits
                        str(len(list(repo.iter_pulls()))),            # number of pulls
                        str(len(list(repo.iter_issues()))),           # number of issues
                        str(repo.forks),                              # number of forks
                        str(len(list(repo.iter_contributors()))),     # number of contributors
                        str(repo.watchers),                           # number of subscribers
                        str(repo.stargazers or 0),                    # number of ♥
                        # info
                        repo.language or '?',                      # language
                        repo.updated_at.strftime(date_fmt),      # date
                        '/'.join([user, repo.name]),             # name
                    ]))
                except Exception as err:
                    if 'Git Repository is empty.' == err.args[0].json()['message']:
                        print('\t'.join([
                            # status
                            'E',
                            # stats
                            'ø',          # number of commits
                            'ø',            # number of pulls
                            'ø',           # number of issues
                            'ø',                              # number of forks
                            'ø',     # number of contributors
                            'ø',                           # number of subscribers
                            'ø',                    # number of ♥
                            # info
                            '?',                      # language
                            repo.updated_at.strftime(date_fmt),      # date
                            '/'.join([user, repo.name]),             # name
                        ]))
                    else:
                        print("Cannot show repository {}: {}".format('/'.join([user, repo.name]), err))

    def get_repository(self, user, repo):
        repository = self.gh.repository(user, repo)
        if not repository:
            raise ResourceNotFoundError('Cannot delete: repository {}/{} does not exists.'.format(user, repo))
        return repository

    def _format_gist(self, gist):
        return gist.split('https://gist.github.com/')[-1].split('.git')[0]

    def gist_list(self, gist=None):
        if not gist:
            for gist in self.gh.iter_gists(self.gh.user().login):
                yield (gist.html_url, gist.description)
        else:
            gist = self.gh.gist(self._format_gist(gist))
            if gist is None:
                raise ResourceNotFoundError('Gist does not exists.')
            for gist_file in gist.iter_files():
                yield (gist_file.language if gist_file.language else 'Raw text',
                        gist_file.size,
                        gist_file.filename)


    def gist_fetch(self, gist, fname=None):
        try:
            gist = self.gh.gist(self._format_gist(gist))
        except Exception as err:
            raise ResourceNotFoundError('Error while fetching gist') from err
        if not gist:
            raise ResourceNotFoundError('Could not find gist')
        if gist.files == 1 and not fname:
            gist_file = list(gist.iter_files())[0]
        else:
            for gist_file in gist.iter_files():
                if gist_file.filename == fname:
                    break
            else:
                raise ResourceNotFoundError('Could not find file within gist.')

        return gist_file.content

    def gist_clone(self, gist):
        try:
            gist = self.gh.gist(gist.split('https://gist.github.com/')[-1])
        except Exception as err:
            raise ResourceNotFoundError('Could not find gist') from err
        remote = self.repository.create_remote('gist', gist.git_push_url)
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
                    local_branch_name = 'requests/github/{}'.format(request)
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
        import platform
        gh = github3.GitHub()
        gh.login(login, password, two_factor_callback=lambda: prompt('2FA code> '))
        try:
            auth = gh.authorize(login, password,
                    scopes=[ 'repo', 'delete_repo', 'gist' ],
                    note='git-repo2 token used on {}'.format(platform.node()),
                    note_url='https://github.com/guyzmo/git-repo')
            return auth.token
        except github3.models.GitHubError as err:
            if len(err.args) > 0 and 422 == err.args[0].status_code:
                raise ResourceExistsError("A token already exist for this machine on your github account.")
            else:
                raise err

    @property
    def user(self):
        return self.gh.user().login

