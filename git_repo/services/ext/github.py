#!/usr/bin/env python3

import logging
log = logging.getLogger('git_repo.github')

from ..service import register_target, RepositoryService, os
from ...exceptions import ResourceError, ResourceExistsError, ResourceNotFoundError, ArgumentError
from ...tools import columnize

import github3

from git.exc import GitCommandError

from datetime import datetime

GITHUB_COM_FQDN = 'github.com'

@register_target('hub', 'github')
class GithubService(RepositoryService):
    fqdn = GITHUB_COM_FQDN

    def __init__(self, *args, **kwarg):
        self.gh = github3.GitHub()
        super(GithubService, self).__init__(*args, **kwarg)

    def connect(self):
        if self.fqdn != GITHUB_COM_FQDN:
            # upgrade self.gh from a GitHub object to a GitHubEnterprise object
            gh = github3.GitHubEnterprise(RepositoryService.build_url(self))
            self.gh._session.base_url = gh._session.base_url
            gh._session = self.gh._session
            self.gh = gh
            # propagate ssl certificate parameter
            self.gh._session.verify = self.session_certificate or not self.session_insecure
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
            self.add(user=user, repo=repo, tracking=self.name)

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
        if not self.gh.user(user):
            raise ResourceNotFoundError("User {} does not exists.".format(user))

        repositories = self.gh.iter_user_repos(user)
        if not _long:
            repositories = list(["/".join([user, repo.name]) for repo in repositories])
            yield "{}"
            yield ("Total repositories: {}".format(len(repositories)),)
            yield from columnize(repositories)
        else:
            yield "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{:12}\t{}"
            yield ['Status', 'Commits', 'Reqs', 'Issues', 'Forks', 'Coders', 'Watch', 'Likes', 'Lang', 'Modif', 'Name']
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
                    nb_pulls = len(list(repo.iter_pulls()))
                    nb_issues = len(list(repo.iter_issues())) - nb_pulls
                    yield [
                        # status
                        status,
                        # stats
                        str(len(list(repo.iter_commits()))),          # number of commits
                        str(nb_pulls),                                # number of pulls
                        str(nb_issues),                               # number of issues
                        str(repo.forks),                              # number of forks
                        str(len(list(repo.iter_contributors()))),     # number of contributors
                        str(repo.watchers),                           # number of subscribers
                        str(repo.stargazers or 0),                    # number of ♥
                        # info
                        repo.language or '?',                      # language
                        repo.updated_at.strftime(date_fmt),      # date
                        '/'.join([user, repo.name]),             # name
                    ]
                except Exception as err:
                    if 'Git Repository is empty.' == err.args[0].json()['message']:
                        yield [
                            # status
                            'E',
                            # stats
                            'ø',     # number of commits
                            'ø',     # number of pulls
                            'ø',     # number of issues
                            'ø',     # number of forks
                            'ø',     # number of contributors
                            'ø',     # number of subscribers
                            'ø',     # number of ♥
                            # info
                            '?',     # language
                            repo.updated_at.strftime(date_fmt),      # date
                            '/'.join([user, repo.name]),             # name
                        ]
                    else:
                        print("Cannot show repository {}: {}".format('/'.join([user, repo.name]), err))

    def _format_gist(self, gist):
        return gist.split('https://gist.github.com/')[-1].split('.git')[0]

    def gist_list(self, gist=None):
        if not gist:
            yield "{:45.45} {}"
            yield 'title', 'url'
            for gist in self.gh.iter_gists(self.gh.user().login):
                yield gist.description, gist.html_url
        else:
            gist = self.gh.gist(self._format_gist(gist))
            if gist is None:
                raise ResourceNotFoundError('Gist does not exists.')
            yield "{:15}\t{:7}\t{}"
            yield 'language', 'size', 'name'
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

    def request_create(self, onto_user, onto_repo, from_branch, onto_branch, title=None, description=None, auto_slug=False, edit=None):
        onto_project = self.gh.repository(onto_user, onto_repo)

        if not onto_project:
            raise ResourceNotFoundError('Could not find project `{}/{}`!'.format(onto_user, onto_repo))

        from_reposlug = self.guess_repo_slug(self.repository, self, resolve_targets=['{service}'])
        if from_reposlug:
            from_user, from_repo = from_reposlug.split('/')
            if (onto_user, onto_repo) == (from_user, from_repo):
                from_project = onto_project
            else:
                from_project = self.gh.repository(from_user, from_repo)
        else:
            from_project = None

        if not from_project:
            raise ResourceNotFoundError('Could not find project `{}`!'.format(from_user, from_repo))

        # when no repo slug has been given to `git-repo X request create`
        # then chances are current project is a fork of the target
        # project we want to push to
        if auto_slug and onto_project.fork:
            onto_user = onto_project.parent.owner.login
            onto_repo = onto_project.parent.name
            onto_project = self.gh.repository(onto_user, onto_repo)

        # if no onto branch has been defined, take the default one
        # with a fallback on master
        if not from_branch:
            from_branch = self.repository.active_branch.name

        # if no from branch has been defined, chances are we want to push
        # the branch we're currently working on
        if not onto_branch:
            onto_branch = self.get_project_default_branch(onto_project)

        from_target = '{}:{}'.format(from_user, from_branch)
        onto_target = '{}/{}:{}'.format(onto_user, onto_project, onto_branch)

        # translate from github username to git remote name
        if not title and not description and edit:
            title, description = edit(self.repository, from_branch, onto_target)
            if not title and not description:
                raise ArgumentError('Missing message for request creation')

        try:
            request = onto_project.create_pull(title,
                    head=from_target,
                    base=onto_branch,
                    body=description)

            yield '{}'
            yield ['Successfully created request of `{local}` onto `{project}:{remote}, with id `{ref}'.format(
                local=from_branch,
                project='/'.join([onto_user, onto_repo]),
                remote=onto_branch,
                ref=request.number
            )]
            yield ['available at {}'.format(request.html_url)]

        except github3.models.GitHubError as err:
            if err.code == 422:
                if err.message == 'Validation Failed':
                    for error in err.errors:
                        if 'message' in error:
                            raise ResourceError(error['message'])
                        if error.get('code', '') == 'invalid':
                            if error.get('field', '') == 'head':
                                raise ResourceError(
                                        'Invalid source branch. ' \
                                        'Check it has been pushed first.')
                            if error.get('field', '') == 'base':
                                raise ResourceError( 'Invalid target branch.')
                    raise ResourceError("Unhandled formatting error: {}".format(err.errors))
            raise ResourceError(err.message)

    def request_list(self, user, repo):
        repository = self.gh.repository(user, repo)
        yield "{}\t{:<60}\t{}"
        yield 'id', 'title', 'URL'
        for pull in repository.iter_pulls():
            yield str(pull.number), pull.title, pull.links['html']

    def request_fetch(self, user, repo, request, pull=False, force=False):
        if pull:
            raise NotImplementedError('Pull operation on requests for merge are not yet supported')
        try:
            remote_names = list(self._convert_user_into_remote(user))
            for remote in self.repository.remotes:
                if remote.name in remote_names:
                    local_branch_name = 'requests/{}/{}'.format(self.name,request)
                    self.fetch(
                        remote,
                        'pull/{}/head'.format(request),
                        local_branch_name,
                        force=force
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
        if cls.fqdn != GITHUB_COM_FQDN:
            gh = github3.GitHubEnterprise()
        else:
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

    def get_parent_project_url(self, user, project, rw=True):
        parent = self.gh.repository(user, project).parent
        if not parent:
            return None
        return self.format_path(
                repository=parent.name,
                namespace=parent.owner.login,
                rw=rw)

    @property
    def user(self):
        return self.gh.user().login

    def get_repository(self, user, repo):
        repository = self.gh.repository(user, repo)
        if not repository:
            raise ResourceNotFoundError('Cannot delete: repository {}/{} does not exists.'.format(user, repo))
        return repository

    @staticmethod
    def is_repository_empty(project):
        return project.size == 0

    @staticmethod
    def get_project_default_branch(project):
       return project.default_branch or 'master'

