#!/usr/bin/env python3

import logging
log = logging.getLogger('git_repo.bitbucket')

from ..service import register_target, RepositoryService, ProgressBar
from ...exceptions import ResourceError, ResourceExistsError, ResourceNotFoundError
from ...tools import columnize

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

from git.exc import GitCommandError

from lxml import html
import os, json, platform


@register_target('bb', 'bitbucket')
class BitbucketService(RepositoryService):
    fqdn = 'bitbucket.org'

    def __init__(self, *args, **kwarg):
        self.bb = Bitbucket(Client())
        super(BitbucketService, self).__init__(*args, **kwarg)

    def connect(self):
        if self._privatekey and ':' in self._privatekey:
            login, password = self._privatekey.split(':')
        else:
            login = self._username
            password = self._privatekey

        if not login or not password:
            raise ConnectionError('Could not connect to BitBucket. Please configure .gitconfig with your bitbucket credentials.')

        auth = BasicAuthenticator(login, password, 'z+git-repo+pub@m0g.net')
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
        try:
            user = User.find_user_by_username(user)
        except HTTPError as err:
            raise ResourceNotFoundError("User {} does not exists.".format(user)) from err

        repositories = user.repositories()
        if not _long:
            yield "{}"
            repositories = list(repositories)
            yield ("Total repositories: {}".format(len(repositories)),)
            yield from columnize(["/".join([user.username, repo.name]) for repo in repositories])
        else:
            yield "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{:12}\t{}"
            yield ['Status', 'Commits', 'Reqs', 'Issues', 'Forks', 'Coders', 'Watch', 'Likes', 'Lang', 'Modif', 'Name']
            for repo in repositories:
                # if repo.updated_at.year < datetime.now().year:
                #     date_fmt = "%b %d %Y"
                # else:
                #     date_fmt = "%b %d %H:%M"

                status = ''.join([
                    'F' if getattr(repo, 'parent', None) else ' ', # is a fork?
                    'P' if repo.is_private else ' ',               # is private?
                ])
                yield [
                    # status
                    status,
                    # stats
                    str(len(list(repo.commits()))),       # number of commits
                    str(len(list(repo.pullrequests()))),  # number of pulls
                    str('N.A.'),                          # number of issues
                    str(len(list(repo.forks()))),         # number of forks
                    str('N.A.'),                          # number of contributors
                    str(len(list(repo.watchers()))),      # number of subscribers
                    str('N.A.'),                          # number of ♥
                    # info
                    repo.language or '?',                 # language
                    repo.updated_on,                      # date
                    '/'.join([user.username, repo.name]), # name
                ]

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

    def request_create(self, onto_user, onto_repo, from_branch, onto_branch, title=None, description=None, auto_slug=False, edit=None):
        try:
            onto_project = self.get_repository(onto_user, onto_repo)

            from_reposlug = self.guess_repo_slug(self.repository, self, resolve_targets=['{service}'])
            if from_reposlug:
                from_user, from_repo = from_reposlug.split('/')
                if (onto_user, onto_repo) == (from_user, from_repo):
                    from_project = onto_project
                else:
                    from_project = self.get_repository(from_user, from_repo)
            else:
                from_project = None

            # when no repo slug has been given to `git-repo X request create`
            # then chances are current project is a fork of the target
            # project we want to push to
            if auto_slug and onto_project.fork:
                onto_user = onto_project.parent.owner.login
                onto_repo = onto_project.parent.name
                onto_project = self.repository(onto_user, onto_repo)

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

            request = PullRequest.create(
                        PullRequestPayload(
                            payload=dict(
                                title=title,
                                description=description or '',
                                destination=dict(
                                    branch=dict(name=onto_branch)
                                ),
                                source=dict(
                                    repository=dict(full_name='/'.join([from_user, from_repo])),
                                    branch=dict(name=from_branch)
                                )
                            )
                        ),
                        repository_name=onto_repo,
                        owner=onto_user,
                        client=self.bb.client
                    )

            yield '{}'
            yield ['Successfully created request of `{local}` onto `{project}:{remote}, with id `{ref}'.format(
                local=from_branch,
                project='/'.join([onto_user, onto_repo]),
                remote=onto_branch,
                ref=request.id
            )]
            yield ['available at {}'.format(request.links['html']['href'])]

        except HTTPError as err:
            status_code = hasattr(err, 'code') and err.code or err.response.status_code
            if 404 == status_code:
                raise ResourceNotFoundError("Couldn't create request, project not found: {}".format(onto_repo)) from err
            elif 400 == status_code and 'branch not found' in err.format_message():
                raise ResourceNotFoundError("Couldn't create request, branch not found: {}".format(from_branch)) from err
            raise ResourceError("Couldn't create request: {}".format(err)) from err

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
        if pull:
            raise NotImplementedError('Pull operation on requests for merge are not yet supported')

        pb = ProgressBar()
        pb.setup(self.name)

        try:
            local_branch_name = 'requests/bitbucket/{}'.format(request)
            pr = next(self.bb.repositoryPullRequestByPullRequestId(
                owner=user,
                repository_name=repo,
                pullrequest_id=request
            ))
            source_branch = pr.source['branch']['name']
            source_slug = pr.source['repository']['full_name']
            source_url = pr.source['repository']['links']['html']['href']
            remote_name = 'requests/bitbucket/{}'.format(source_slug).replace('/', '-')
            try:
                remote = self.repository.remote(name=remote_name)
            except ValueError:
                remote = self.repository.create_remote(name=remote_name, url=source_url)
            refspec = '{}:{}'.format(source_branch, local_branch_name)
            refs = remote.fetch(refspec, progress=pb)
            for branch in self.repository.branches:
                if branch.name == local_branch_name:
                    branch.set_tracking_branch(remote.refs[0])
            return local_branch_name
        except HTTPError as err:
            if '404' in err.args[0].split(' '):
                raise ResourceNotFoundError('Could not find opened request #{}'.format(request)) from err
            raise ResourceError("Couldn't delete snippet: {}".format(err)) from err
        except GitCommandError as err:
            if 'Error when fetching: fatal: ' in err.command[0]:
                raise ResourceNotFoundError('Could not find opened request #{}'.format(request)) from err
            raise err

    @classmethod
    def get_auth_token(cls, login, password, prompt=None):
        session = Session()

        key_name = 'git-repo@{}'.format(platform.node())

        # get login page
        log.info('» Login to bitbucket…')

        login_url = "https://bitbucket.org/account/signin/?next=/".format(login)

        session.headers.update({
            "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) " \
            "AppleWebKit/537.36 (KHTML, like Gecko) " \
            "Chrome/52.0.2743.82 Safari/537.36"
        })

        result = session.get(login_url)
        tree = html.fromstring(result.text)

        # extract CSRF token

        authenticity_token = list(set(tree.xpath("//input[@name='csrfmiddlewaretoken']/@value")))[0]

        # do login

        payload = {
            'username': login,
            'password': password,
            'csrfmiddlewaretoken': authenticity_token
        }

        result = session.post(
            login_url,
            data = payload,
            headers = dict(referer=login_url)
        )
        tree = html.fromstring(result.text)

        # extract username

        try:
            username = json.loads(tree.xpath('//meta/@data-current-user')[0])['username']
        except KeyError:
            raise ResourceNotFoundError('Invalid login. Please make sure you\'re using your bitbucket email address as username!')

        app_password_url ='https://bitbucket.org/account/user/{}/app-passwords/new'.format(username)

        # load app password page
        log.info('» Generating app password…')

        result = session.get(
            app_password_url,
            headers=dict(referer=app_password_url)
        )
        tree = html.fromstring(result.content)

        if 'git-repo@{}'.format(platform.node()) in result:
            log.warn("A duplicate key is being created!")

        # generate app password
        log.info('» App password is setup with following scopes:')
        log.info('»     account, team, project:write, repository:admin, repository:delete')
        log.info('»     pullrequest:write, snippet, snippet:write')

        authenticity_token = list(set(tree.xpath("//input[@name='csrfmiddlewaretoken']/@value")))[0]

        payload = dict(
            name=key_name,
            scope=['account',
                    'team',
                    'project',
                    'project:write',
                    'repository',
                    'pullrequest:write',
                    'repository:admin',
                    'repository:delete',
                    'snippet',
                    'snippet:write'
                    ],
            csrfmiddlewaretoken=authenticity_token
        )
        result = session.post(
            app_password_url,
            data=payload,
            headers=dict(referer=app_password_url)
        )
        tree = html.fromstring(result.content)

        password = json.loads(tree.xpath('//section/@data-app-password')[0])['password']

        return password

    def get_parent_project_url(self, user, project, rw=True):
        project = self.get_repository(user, project)
        if not project or not hasattr(project, 'parent') or not project.parent:
            return None
        return self.format_path(
            repository=project.parent.name,
            namespace=project.parent.owner.login,
            rw=True)

    @property
    def user(self):
        try:
            user = next(self.bb.userForMyself()).username
            return user
        except (HTTPError, AttributeError) as err:
            raise ResourceError("Couldn't find the current user: {}".format(err)) from err


    def get_repository(self, user, repo):
        try:
            return next(self.bb.repositoryByOwnerAndRepositoryName(owner=user, repository_name=repo))
        except HTTPError as err:
            raise ResourceNotFoundError('Cannot retrieve repository: {}/{} does not exists.'.format(user, repo))

    @staticmethod
    def is_repository_empty(project):
        return project.size == 0

    @staticmethod
    def get_project_default_branch(project):
        return project.mainbranch.get('name', 'master')
