#!/usr/bin/env python

from ..service import register_target, RepositoryService

from gerritclient import client
from gerritclient.error import HTTPError

@register_target('gerrit', 'gerrit')
class GerritService(RepositoryService):
    fqdn = 'review.gerrithub.io'
    auth_type = 'basic'
    ssh_port = 29418
    _max_nested_namespaces = 99
    _min_nested_namespaces = 0
    ro_suffix = ''

    def create_connection(self):
        self.connection = client.connect(self.url_ro, auth_type=self.auth_type,
                                    username=self._username, password=self._privatekey)
        self._session = self.connection.session

    def connect(self):
        if not hasattr(self, 'connection'):
            self.create_connection()
        self.server_client = client.get_client('server', connection=self.connection)
        self.project_client = client.get_client('project', connection=self.connection)

        try:
            self.server_client.get_version()
        except HTTPError as err:
            if not self._username or not self._privatekey:
                raise ConnectionError('Could not connect to Gerrit. '
                                      'Please configure .gitconfig '
                                      'with your gerrit username and HTTP password.') from err
            else:
                raise ConnectionError('Could not connect to Gerrit. '
                                      'Please check your configuration and try again.') from err

    @classmethod
    def get_auth_token(self, login, password, prompt=None):
        # HTTP password is used as auth token
        return password

    def load_configuration(self, c, hc=[]):
        super(GerritService, self).load_configuration(c, hc)
        self.ssh_port = c.get('ssh-port', self.ssh_port)
        self.auth_type = c.get('auth-type', self.auth_type)
        self.ro_suffix = c.get('ro-suffix', self.ro_suffix)

    @property
    def session(self):
        if not hasattr(self, '_session'):
            self.create_connection()
        return self._session

    @property
    def git_user(self):
        return self._username

    @property
    def url_ro(self):
        '''Property that returns the HTTP URL of the service'''
        return self.build_url(self) + self.ro_suffix

    @property
    def url_rw(self):
        return 'ssh://{}@{}:{}'.format(self.git_user, self.ssh_url, self.ssh_port)

    def repo_name(self, namespace, repo):
        if namespace:
            return '{}/{}'.format(namespace, repo)
        else:
            return repo

    def get_repository(self, namespace, repo):
        if namespace is not None:
            return self.project_client.get_by_name(self.repo_name(namespace, repo))
        else:
            return self.project_client.get_by_name(repo)

    def get_project_default_branch(self, project):
        branches = self.project_client.get_branches(project['name'])
        for branch in branches:
            if branch['ref'] == 'HEAD':
                return branch['revision']

    def is_repository_empty(self, project):
        # There is no way to find out if repository is empty, so always return False
        return False

    def get_parent_project_url(self, namespace, repo, rw=True):
        # Gerrit parent project concept is quite different from other services,
        # so it is better to always return None here
        return None
