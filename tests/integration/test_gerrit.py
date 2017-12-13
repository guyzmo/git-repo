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
