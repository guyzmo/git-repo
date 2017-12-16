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

    def test_00_clone(self):
        self.action_clone(namespace='TestUser',
                          repository='DemoRepository')

    def test_01_review(self):
        self.action_request_create_by_push(namespace='TestUser',
                                           repository='DemoRepository',
                                           branch='master',
                                           remote_ref='refs/for/master')

    def test_02_fetch_patchset(self):
        self.action_request_fetch(namespace='TestUser',
                                  repository='DemoRepository',
                                  request='392089',
                                  remote_ref='refs/changes/89/392089/2',
                                  local_ref='requests/gerrithub/392089')

    def test_03_fetch_patchset__patchset(self):
        self.action_request_fetch(namespace='TestUser',
                                  repository='DemoRepository',
                                  request='392089/1',
                                  remote_ref='refs/changes/89/392089/1',
                                  local_ref='requests/gerrithub/392089')

    def test_04_fetch_patchset__full(self):
        self.action_request_fetch(namespace='TestUser',
                                  repository='DemoRepository',
                                  request='refs/changes/08/391808/2',
                                  remote_ref='refs/changes/08/391808/2',
                                  local_ref='requests/gerrithub/391808')

    def test_05_fetch_patchset__change_id(self):
        self.action_request_fetch(namespace='TestUser',
                                  repository='DemoRepository',
                                  request='I873f1207d6',
                                  remote_ref='refs/changes/89/392089/2',
                                  local_ref='requests/gerrithub/392089')
