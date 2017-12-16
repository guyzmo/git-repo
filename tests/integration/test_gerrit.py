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

    def action_request_fetch(self, namespace, repository, request, ref):
        local_slug = self.service.format_path(namespace=namespace, repository=repository, rw=True)
        self.repository.create_remote('all', url=local_slug)
        self.repository.create_remote(self.service.name, url=local_slug)

        with self.mockup_git(namespace, repository):
            self.set_mock_popen_commands([
                ('git version', b'git version 2.7.4', b'', 0),
                ('git fetch --progress --update-head-ok -v gerrithub {}'.format(ref), b'', '\n'.join([
                    'From {}'.format(local_slug),
                    '* branch            {} -> FETCH_HEAD'.format(ref)
                ]).encode('utf-8'), 0),
                ('git checkout FETCH_HEAD', b'', '\n'.join([
                    'Note: checking out \'FETCH_HEAD\'',
                    '',
                    'You are in \'detached HEAD\' state. You can look around, make experimental',
                    'changes and commit them, and you can discard any commits you make in this',
                    'state without impacting any branches by performing another checkout.',
                    '',
                    'If you want to create a new branch to retain commits you create, you may',
                    'do so (now or later) by using -b with the checkout command again. Example:',
                    '',
                    '  git checkout -b <new-branch-name>',
                    '',
                    'HEAD is now at 5bb7935... One more test',
                ]).encode('utf-8'), 0)
            ])
            with self.recorder.use_cassette(self._make_cassette_name()):
                self.service.connect()
                self.service.request_fetch(namespace, repository, request)

    def test_00_clone(self):
        self.action_clone(namespace='TestUser',
                          repository='DemoRepository')

    def test_01_review(self):
        self.action_request_create(namespace='TestUser', repository='DemoRepository', branch='master')

    def test_02_fetch_patchset(self):
        self.action_request_fetch(namespace='TestUser', repository='DemoRepository', request='392089', ref='refs/changes/89/392089/2')

    def test_03_fetch_patchset__patchset(self):
        self.action_request_fetch(namespace='TestUser', repository='DemoRepository', request='392089/1', ref='refs/changes/89/392089/1')

    def test_04_fetch_patchset__full(self):
        self.action_request_fetch(namespace='TestUser', repository='DemoRepository', request='refs/changes/08/391808/2', ref='refs/changes/08/391808/2')

    def test_05_fetch_patchet__change_id(self):
        self.action_request_fetch(namespace='TestUser', repository='DemoRepository', request='I873f1207d6', ref='refs/changes/89/392089/2')
