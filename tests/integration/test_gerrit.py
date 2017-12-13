#!/usr/bin/env python

import logging

#################################################################################
# Enable logging

log = logging.getLogger('test.gerrit')

#################################################################################

from tests.helpers import GitRepoTestCase

from git_repo.services.service import gerrit

class Test_Gerrit(GitRepoTestCase):
    log = log

    def get_service(self):
        return gerrit.GerritService(c={
            '__name__': 'gitrepo "gerrithub"',
            'fqdn': 'review.gerrithub.io',
            'username': 'TestUser',
            'token': 'test_token'
        })

    def get_requests_session(self):
        return self.service.session

    def action_request_create(self, namespace, repository, branch):
        local_slug = self.service.format_path(namespace=namespace, repository=repository, rw=True)
        self.repository.create_remote('all', url=local_slug)
        self.repository.create_remote(self.service.name, url=local_slug)

        with self.mockup_git(namespace, repository):
            self.set_mock_popen_commands([
                ('git version', b'git version 2.7.4', b'', 0),
                ('git push --porcelain --progress {} HEAD:refs/for/{}'.format(self.service.name, branch), b'', '\n'.join([
                    'Counting objects: 6, done.',
                    'Delta compression using up to 2 threads.',
                    'Compressing objects: 100% (6/6), done.',
                    'Writing objects: 100% (6/6), 515 bytes | 0 bytes/s, done.',
                    'Total 6 (delta 4), reused 0 (delta 0)',
                    'remote: Resolving deltas: 100% (4/4)',
                    'remote: Processing changes: new: 1, refs: 1, done',
                    'remote: ',
                    'remote: New Changes:',
                    'remote:   https://{}/391808 One more test'.format(self.service.fqdn),
                    'remote: ',
                    'To {}'.format(local_slug),
                    '*	HEAD:refs/for/{}	[new branch]'.format(branch),
                    'Done'
                ]).encode('utf-8'), 0)
            ])
            with self.recorder.use_cassette(self._make_cassette_name()):
                self.service.connect()
                self.service.request_create(namespace, repository, branch)

    def test_00_clone(self):
        self.action_clone(namespace='TestUser',
                          repository='DemoRepository')

    def test_01_review(self):
        self.action_request_create(namespace='TestUser', repository='DemoRepository', branch='master')
