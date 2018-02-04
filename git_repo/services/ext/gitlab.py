#!/usr/bin/env python3

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

    _max_nested_namespaces = 21

    def __init__(self, *args, **kwarg):
        self.session = gitlab.requests.Session()
        super().__init__(*args, **kwarg)

    def connect(self):
        if self.session_proxy:
            self.gl.session.proxies.update(self.session_proxy)

        self.gl = gitlab.Gitlab(self.url_ro,
                session=self.session,
                private_token=self._privatekey
        )

        self.gl.ssl_verify = self.session_certificate or not self.session_insecure

        self.gl.auth()
        self.username = self.gl.user.username

    def create(self, user, repo, add=False):
        try:
            group = self.gl.groups.search(user)
            data = {'name': repo, 'path': repo}
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

        repositories = self.gl.projects.list(author=user, safe_all=True)
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
                    str(len(repo.commits.list(all=True))),       # number of commits
                    str(len(repo.mergerequests.list(all=True))), # number of pulls
                    str(len(repo.issues.list(all=True))),        # number of issues
                    str(repo.forks_count),                     # number of forks
                    str(len(repo.members.list(all=True))),       # number of contributors
                    'N.A.',                                    # number of subscribers
                    str(repo.star_count),                      # number of ♥
                                                               # info
                    'N.A.',                                    # language
                    repo_last_activity_at.strftime(date_fmt),  # date
                    repo.name_with_namespace,                  # name
                ]

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

    def request_create(self, onto_user, onto_repo, from_branch, onto_branch, title=None, description=None, auto_slug=False, edit=None):
        try:
            onto_project = self.gl.projects.get('/'.join([onto_user, onto_repo]))

            if not onto_project:
                raise ResourceNotFoundError('Could not find project `{}/{}`!'.format(onto_user, onto_repo))

            from_reposlug = self.guess_repo_slug(self.repository, self, resolve_targets=['{service}'])
            if from_reposlug:
                *namespaces, from_repo = from_reposlug.split('/')
                from_user = '/'.join(namespaces)
                if (onto_user, onto_repo) == (from_user, from_repo):
                    from_project = onto_project
                else:
                    from_project = self.gl.projects.get('/'.join([from_user, from_repo]))
            else:
                from_project = None

            if not from_project:
                raise ResourceNotFoundError('Could not find project `{}`!'.format(from_reposlug))

            # when no repo slug has been given to `git-repo X request create`
            # then chances are current project is a fork of the target
            # project we want to push to
            if auto_slug and 'forked_from_project' in onto_project.as_dict():
                parent = self.gl.projects.get(onto_project.forked_from_project['id'])
                onto_user, onto_repo = parent.namespace.path, parent.path
                onto_project = self.gl.projects.get('/'.join([onto_user, onto_repo]))

            # if no onto branch has been defined, take the default one
            # with a fallback on master
            if not from_branch:
                from_branch = self.repository.active_branch.name
            # if no from branch has been defined, chances are we want to push
            # the branch we're currently working on
            if not onto_branch:
                onto_branch = self.get_project_default_branch(onto_project)

            onto_target = '{}:{}'.format(onto_user, onto_project.path_with_namespace, onto_branch)

            # translate from gitlab username to git remote name
            if not title and not description and edit:
                title, description = edit(self.repository, from_branch, onto_target)
                if not title and not description:
                    raise ArgumentError('Missing message for request creation')

            request = self.gl.project_mergerequests.create(
                    project_id=from_project.id,
                    data={
                        'source_branch': from_branch,
                        'target_branch': onto_branch,
                        'target_project_id': onto_project.id,
                        'title': title,
                        'description': description
                    }
            )

            yield '{}'
            yield ['Successfully created request of `{local}` onto `{project}:{remote}, with id `{ref}'.format(
                local=from_branch,
                project='/'.join([onto_user, onto_repo]),
                remote=onto_branch,
                ref=request.iid
            )]
            yield ['available at {}'.format(request.web_url)]

        except GitlabGetError as err:
            raise ResourceNotFoundError(err) from err
        except Exception as err:
            raise ResourceError("Unhandled error: {}".format(err)) from err

    def request_list(self, user, repo):
        project = self.gl.projects.get('/'.join([user, repo]))
        yield "{:>3}\t{:<60}\t{:2}"
        yield ('id', 'title', 'URL')
        for mr in self.gl.project_mergerequests.list(project_id=project.id):
            yield ( str(mr.iid),
                    mr.title,
                    mr.web_url
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
                       'merge-requests/{}/head'.format(request),
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

    def get_parent_project_url(self, user, repo, rw=True):
        project = self.gl.projects.get('/'.join([user, repo]))
        parent = None
        if hasattr(project, 'forked_from_project'):
            parent = self.gl.projects.get(project.forked_from_project['id'])
        if not parent:
            return None
        return self.format_path(
                repository=parent.path,
                namespace=parent.namespace.path,
                rw=rw)

    @property
    def user(self):
        return self.gl.user.username

    def get_repository(self, user, repo):
        try:
            return self.gl.projects.get('{}/{}'.format(user, repo))
        except GitlabGetError as err:
            if err.response_code == 404:
                raise ResourceNotFoundError("Cannot get: repository {}/{} does not exists.".format(user, repo)) from err

    @staticmethod
    def get_project_default_branch(project):
        return project.default_branch or 'master'

    @staticmethod
    def is_repository_empty(project):
        try:
            project.repository_tree()
            return True
        except gitlab.exceptions.GitlabGetError:
            return False

