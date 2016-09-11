#!/usr/bin/env python

import logging
log = logging.getLogger('git_repo.gitlab')

from ..service import register_target, RepositoryService
from ...exceptions import ArgumentError, ResourceError, ResourceExistsError, ResourceNotFoundError

import gitlab
from gitlab.exceptions import GitlabCreateError, GitlabGetError

import json

@register_target('lab', 'gitlab')
class GitlabService(RepositoryService):
    fqdn = 'gitlab.com'

    def __init__(self, *args, **kwarg):
        self.gl = gitlab.Gitlab(self.url_ro)
        super(GitlabService, self).__init__(*args, **kwarg)

    def connect(self):
        self.gl.set_token(self._privatekey)
        self.gl.token_auth()
        self.username = self.gl.user.username

    def create(self, user, repo, add=False):
        try:
            self.gl.projects.create(data={
                'name': repo,
                # 'namespace_id': user, # TODO does not work, cannot create on
                # another namespace yet
            })
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

    def get_repository(self, user, repo):
        try:
            return self.gl.projects.get('{}/{}'.format(user, repo))
        except GitlabGetError as err:
            if err.response_code == 404:
                raise ResourceNotFoundError("Cannot get: repository {}/{} does not exists.".format(user, repo)) from err

    @classmethod
    def get_auth_token(cls, login, password):
        gl = gitlab.Gitlab(url='https://{}'.format(cls.fqdn), email=login, password=password)
        gl.auth()
        return gl.user.private_token

    # def _format_gist(self, gist):
    #     return gist.split('https://gist.github.com/')[-1].split('.git')[0]

    def gist_list(self, project=None):
        if not project:
            for project in self.gl.projects.list(per_page=100):
                for snippet in project.snippets.list(per_page=100):
                    yield ('https://{}/{}/{}/snippets/{}'.format(
                            self.fqdn,
                            snippet.author.username,
                            project.name,
                            snippet.id
                        ), snippet.title)
            log.warn('Global snippets are still not supported in gitlab API.')
            log.warn('Only listing projects\' snippets!')
        else:
            project = self.gl.projects.list(search=project)
            if len(project):
                project = project[0]
            for snippet in project.snippets.list(per_page=100):
                yield ('https://{}/{}/{}/snippets/{}'.format(
                        self.fqdn,
                        snippet.author.username,
                        project.name,
                        snippet.id
                    ), 0, snippet.title)

    def _deconstruct_snippet_uri(self, uri):
        path = uri.split('https://{}/'.format(self.fqdn))[-1]
        user, project_name, _, snippet_id = path.split('/')
        return (user, project_name, snippet_id)

    def gist_fetch(self, snippet, fname=None):
        if fname:
            raise ArgumentError('Snippets contain only single file in gitlab.')

        try:
            _, project_name, snippet_id = self._deconstruct_snippet_uri(snippet)
            project = self.gl.projects.list(search=project_name)[0]
            snippet = self.gl.project_snippets.get(project_id=project.id, id=snippet_id)
        except Exception as err:
            raise ResourceNotFoundError('Could not find snippet') from err

        return snippet.Content().decode('utf-8')

    def gist_clone(self, gist):
        raise ArgumentError('Snippets cannot be cloned in gitlab.')

    def gist_create(self, gist_pathes, description, secret=False):
        raise NotImplementedError

        # ISSUE: how to implement the missing "project" parameter?

        def load_file(fname, path='.'):
            with open(os.path.join(path, fname), 'r') as f:
                return {'code': f.read()}

        if len(gist_pathes) != 1:
            raise ArgumentError('Snippets contain only single file in gitlab.')

        gist_path = gist_pathes[0]

        data = {
                'id': project.id,
                'title': description,
                'file_name': os.path.basename(gist_path),
                'visibility_level': 0 if secret else 20
                }
        data.update(load_file(gist_path))

        gist = self.gl.project_snippets.create(data)

        return gist.html_url

    def gist_delete(self, gist_id):
        if fname:
            raise ArgumentError('Snippets contain only a single file in gitlab.')

        try:
            _, project_name, snippet_id = self._deconstruct_snippet_uri(snippet)
            project = self.gl.projects.list(search=project_name)[0]
            snippet = self.gl.project_snippets.get(project_id=project.id, id=snippet_id)
        except Exception as err:
            raise ResourceNotFoundError('Could not find snippet') from err

        return snippet.delete()

    @property
    def user(self):
        return self.gl.user.username

