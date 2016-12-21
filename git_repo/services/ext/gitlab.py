#!/usr/bin/env python

import logging
log = logging.getLogger('git_repo.gitlab')

from ..service import register_target, RepositoryService
from ...exceptions import ArgumentError, ResourceError, ResourceExistsError, ResourceNotFoundError

import gitlab
from gitlab.exceptions import GitlabCreateError, GitlabGetError

import json, time

@register_target('lab', 'gitlab')
class GitlabService(RepositoryService):
    fqdn = 'gitlab.com'

    def __init__(self, *args, **kwarg):
        super().__init__(*args, **kwarg)
        self.gl = gitlab.Gitlab(self.url_ro, ssl_verify=not self.insecure)

    def connect(self):
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

        if not self.gl.users.search(user):
            raise ResourceNotFoundError("User {} does not exists.".format(user))

        repositories = self.gl.projects.list(author=user)
        if not _long:
            repositories = list(repositories)
            col_print([repo.path_with_namespace for repo in repositories])
        else:
            print('Status\tCommits\tReqs\tIssues\tForks\tCoders\tWatch\tLikes\tLang\tModif\t\tName', file=sys.stderr)
            for repo in repositories:
                time.sleep(0.5)
                # if repo.last_activity_at.year < datetime.now().year:
                #     date_fmt = "%b %d %Y"
                # else:
                #     date_fmt = "%b %d %H:%M"

                status = ''.join([
                    'F' if False else ' ',               # is a fork?
                    'P' if repo.visibility_level == 0 else ' ',            # is private?
                ])
                print('\t'.join([
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
                    repo.last_activity_at,                     # date
                    repo.name_with_namespace,                  # name
                ]))

    def get_repository(self, user, repo):
        try:
            return self.gl.projects.get('{}/{}'.format(user, repo))
        except GitlabGetError as err:
            if err.response_code == 404:
                raise ResourceNotFoundError("Cannot delete: repository {}/{} does not exists.".format(user, repo)) from err

    @classmethod
    def get_auth_token(cls, login, password, prompt=None):
        gl = gitlab.Gitlab(url='https://{}'.format(cls.fqdn), email=login, password=password)
        gl.auth()
        return gl.user.private_token

    @property
    def user(self):
        return self.gl.user.username

