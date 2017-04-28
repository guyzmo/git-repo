#!/usr/bin/env python

import logging
log = logging.getLogger('git_repo.gitlab')

from ..service import register_target, RepositoryService
from ...exceptions import ArgumentError, ResourceError, ResourceExistsError, ResourceNotFoundError
from ...tools import columnize

import gitlab
from gitlab.exceptions import GitlabListError, GitlabCreateError, GitlabGetError

from git.exc import GitCommandError

import os
import json, time
import dateutil.parser
from datetime import datetime

@register_target('lab', 'gitlab')
class GitlabService(RepositoryService):
    fqdn = 'gitlab.com'

    def __init__(self, *args, **kwarg):
        self.gl = gitlab.Gitlab(self.url_ro)
        super().__init__(*args, **kwarg)

    def connect(self):
        self.gl.ssl_verify = self.session_certificate or not self.session_insecure
        if self.session_proxy:
            self.gl.session.proxies.update(self.session_proxy)

        self.gl.set_url(self.url_ro)
        self.gl.set_token(self._privatekey)
        self.gl.token_auth()
        self.username = self.gl.user.username

    def create(self, user, repo, add=False):
        try:
            group = self.gl.groups.search(user)
            data = {'name': repo}
            if group:
                data['namespace_id'] = group[0].id
            self.gl.projects.create(data=data)
        except GitlabCreateError as err:
            if json.loads(err.response_body.decode('utf-8'))['message']['name'][0] == 'has already been taken':
                raise ResourceExistsError("Project already exists.") from err
            else:
                raise ResourceError("Unhandled error.") from err
        if add:
            self.add(user=user, repo=repo, tracking=self.name)

    def fork(self, user, repo):
        try:
            return self.gl.projects.get('{}/{}'.format(user, repo)).forks.create({}).path_with_namespace
        except GitlabCreateError as err:
            if json.loads(err.response_body.decode('utf-8'))['message']['name'][0] == 'has already been taken':
                raise ResourceExistsError("Project already exists.") from err
            else:
                raise ResourceError("Unhandled error: {}".format(err)) from err

    def delete(self, repo, user=None):
        if not user:
            user = self.user
        try:
            repository = self.gl.projects.get('{}/{}'.format(user, repo))
            if repository:
                result = self.gl.delete(repository.__class__, repository.id)
            if not repository or not result:
                raise ResourceNotFoundError("Cannot delete: repository {}/{} does not exists.".format(user, repo))
        except GitlabGetError as err:
            if err.response_code == 404:
                raise ResourceNotFoundError("Cannot delete: repository {}/{} does not exists.".format(user, repo)) from err
            elif err.response_code == 403:
                raise ResourcePermissionError("You don't have enough permissions for deleting the repository. Check the namespace or the private token's privileges") from err
        except Exception as err:
            raise ResourceError("Unhandled exception: {}".format(err)) from err

    def list(self, user, _long=False):
        if not self.gl.users.search(user):
            raise ResourceNotFoundError("User {} does not exists.".format(user))

        repositories = self.gl.projects.list(author=user)
        if not _long:
            repositories = list([repo.path_with_namespace for repo in repositories])
            yield "{}"
            yield ("Total repositories: {}".format(len(repositories)),)
            yield from columnize(repositories)
        else:
            yield "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{:12}\t{}"
            yield ['Status', 'Commits', 'Reqs', 'Issues', 'Forks', 'Coders', 'Watch', 'Likes', 'Lang', 'Modif\t', 'Name']
            for repo in repositories:
                time.sleep(0.5)
                repo_last_activity_at = dateutil.parser.parse(repo.last_activity_at)
                if repo_last_activity_at.year < datetime.now().year:
                    date_fmt = "%b %d %Y"
                else:
                    date_fmt = "%b %d %H:%M"

                status = ''.join([
                    'F' if False else ' ',               # is a fork?
                    'P' if repo.visibility_level == 0 else ' ',            # is private?
                ])
                yield [
                                                               # status
                    status,
                                                               # stats
                    str(len(list(repo.commits.list()))),       # number of commits
                    str(len(list(repo.mergerequests.list()))), # number of pulls
                    str(len(list(repo.issues.list()))),        # number of issues
                    str(repo.forks_count),                     # number of forks
                    str(len(list(repo.members.list()))),       # number of contributors
                    'N.A.',                                    # number of subscribers
                    str(repo.star_count),                      # number of ♥
                                                               # info
                    'N.A.',                                    # language
                    repo_last_activity_at.strftime(date_fmt),  # date
                    repo.name_with_namespace,                  # name
                ]

    def get_repository(self, user, repo):
        try:
            return self.gl.projects.get('{}/{}'.format(user, repo))
        except GitlabGetError as err:
            if err.response_code == 404:
                raise ResourceNotFoundError("Cannot get: repository {}/{} does not exists.".format(user, repo)) from err

    @classmethod
    def get_auth_token(cls, login, password, prompt=None):
        gl = gitlab.Gitlab(url='https://{}'.format(cls.fqdn), email=login, password=password)
        gl.auth()
        return gl.user.private_token

    def _deconstruct_snippet_uri(self, uri):
        path = uri.split('https://{}/'.format(self.fqdn))[-1].split('/')
        if 4 == len(path):
            user, project_name, _, snippet_id = path
        elif 2 == len(path):
            _, snippet_id = path
            project_name = None
            user = None
        elif 1 == len(path):
            snippet_id = path[0]
            project_name = None
            user = None
        else:
            raise ResourceNotFoundError('URL is not of a snippet')
        return (user, project_name, snippet_id)

    def gist_list(self, project=None):
        yield "{:45.45} {}"
        yield 'title', 'url'
        if not project:
            try:
                for snippet in self.gl.snippets.list():
                    yield snippet.title, snippet.web_url
            except GitlabListError as err:
                if err.response_code == 404:
                    raise ResourceNotFoundError('Feature not available, please upgrade your gitlab instance.') from err
                raise ResourceError('Cannot list snippet') from err
        else:
            if '/' not in project:
                project = '/'.join([self.username, project])
            try:
                project = self.gl.projects.get(project)
                for snippet in project.snippets.list():
                    yield (snippet.web_url, snippet.title)
            except GitlabGetError as err:
                raise ResourceNotFoundError('Could not retrieve project "{}".'.format(project)) from err

    def gist_fetch(self, snippet, fname=None):
        if fname:
            raise ArgumentError('Snippets contain only single file in gitlab.')
        try:
            *_, snippet_id = self._deconstruct_snippet_uri(snippet)
            snippet = self.gl.snippets.get(id=snippet_id)
        except GitlabGetError as err:
            if err.response_code == 404:
                if "The page you're looking for could not be found." in err.response_body.decode('utf-8'):
                    raise ResourceNotFoundError('Feature not available, please upgrade your gitlab instance.') from err
                raise ResourceNotFoundError('Cannot fetch snippet') from err
            raise ResourceError('Cannot fetch snippet') from err
        except Exception as err:
            raise ResourceNotFoundError('Could not find snippet') from err

        return snippet.raw().decode('utf-8')

    def gist_clone(self, gist):
        raise ArgumentError('Snippets cannot be cloned in gitlab.')

    def gist_create(self, gist_pathes, description, secret=False):
        def load_file(fname, path='.'):
            with open(os.path.join(path, fname), 'r') as f:
                return f.read()

        if len(gist_pathes) > 2:
            raise ArgumentError('Snippets contain only single file in gitlab.')

        data = {
            'title': description,
            'visibility_level': 0 if secret else 20
        }

        try:

            if len(gist_pathes) == 2:
                project = gist_pathes[0]
                if '/' in project:
                    *namespace, project = project.split('/')
                    namespace = '/'.join(namespace)
                else:
                    namespace = self.username
                gist_path = gist_pathes[1]
                data.update({
                        'project_id': '/'.join([namespace, project]),
                        'code': load_file(gist_path),
                        'file_name': os.path.basename(gist_path),
                    }
                )
                gist = self.gl.project_snippets.create(data)

            elif len(gist_pathes) == 1:
                gist_path = gist_pathes[0]
                data.update({
                        'content': load_file(gist_path),
                        'file_name': os.path.basename(gist_path),
                    }
                )
                gist = self.gl.snippets.create(data)

            return gist.web_url
        except GitlabCreateError as err:
            if err.response_code == 422:
                raise ResourceNotFoundError('Feature not available, please upgrade your gitlab instance.') from err
            raise ResourceError('Cannot create snippet') from err

    def gist_delete(self, snippet):
        try:
            _, project, snippet_id = self._deconstruct_snippet_uri(snippet)
            if project:
                if '/' in project:
                    *namespace, project = project.split('/')
                    namespace = '/'.join(namespace)
                else:
                    namespace = self.username
                snippet = self.gl.projects.get(
                        '/'.join([namespace, project])
                    ).snippets.get(id=snippet_id)
            else:
                snippet = self.gl.snippets.get(id=snippet_id)
        except GitlabCreateError as err:
            if err.response_code == 422:
                raise ResourceNotFoundError('Cannot delete snippet, please upgrade your gitlab instance.') from err
            raise ResourceError('Cannot delete snippet') from err
        except Exception as err:
            raise ResourceNotFoundError('Could not find snippet') from err

        return snippet.delete()

    def request_create(self, user, repo, local_branch, remote_branch, title, description=None, auto_slug=False, edit=None):
        try:
            repository = self.gl.projects.get('/'.join([user, repo]))
            if not repository:
                raise ResourceNotFoundError('Could not find repository `{}/{}`!'.format(user, repo))
            if not title and not description and edit:
                title, description = edit(repository, local_branch)
                if not title and not description:
                    raise ArgumentError('Missing message for request creation')
            if not local_branch:
                local_branch = self.repository.active_branch.name
            if not remote_branch:
                remote_branch = repository.default_branch or 'master'
            request = self.gl.project_mergerequests.create(
                    project_id=repository.id,
                    data= {
                        'source_branch':local_branch,
                        'target_branch':remote_branch,
                        'title':title,
                        'description':description
                        }
                    )
        except GitlabGetError as err:
            raise ResourceNotFoundError(err) from err
        except Exception as err:
            raise ResourceError("Unhandled error: {}".format(err)) from err

        return {'local': local_branch,
                'remote': remote_branch,
                'ref': request.iid}

    def request_list(self, user, repo):
        project = self.gl.projects.get('/'.join([user, repo]))
        yield "{:>3}\t{:<60}\t{:2}"
        yield ('id', 'title', 'URL')
        for mr in self.gl.project_mergerequests.list(project_id=project.id):
            yield ( str(mr.iid),
                    mr.title,
                    'https://{}/{}/{}/merge_requests/{}'.format(
                        self.fqdn,
                        project.namespace.name,
                        project.name,
                        mr.iid
                        )
                    )

    def request_fetch(self, user, repo, request, pull=False, force=False):
        if pull:
            raise NotImplementedError('Pull operation on requests for merge are not yet supported')
        try:
            for remote in self.repository.remotes:
                if remote.name == self.name:
                    local_branch_name = 'requests/gitlab/{}'.format(request)
                    self.fetch(
                        remote,
                       'merge_requests/{}/head'.format(request),
                        local_branch_name,
                        force
                    )
                    return local_branch_name
            else:
                raise ResourceNotFoundError('Could not find remote {}'.format(self.name))
        except GitCommandError as err:
            if 'Error when fetching: fatal: Couldn\'t find remote ref' in err.command[0]:
                raise ResourceNotFoundError('Could not find opened request #{}'.format(request)) from err
            raise err

    @property
    def user(self):
        return self.gl.user.username

