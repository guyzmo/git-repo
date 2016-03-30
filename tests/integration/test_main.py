#!/usr/bin/env python

import logging

#################################################################################
# Enable logging

log = logging.getLogger('test.main')

#################################################################################

from tests.helpers import GitRepoMainTestCase

class Test_Main(GitRepoMainTestCase):
    log = log
    target = 'hub'

    def test_add(self):
        repo_slug, seen_args = self.main_add('guyzmo/git-repo', 0)
        assert ('git-repo', 'guyzmo') == repo_slug
        assert {'name': None,
                'alone': False,
                'tracking': 'master'} == seen_args

    def test_add__alone(self):
        repo_slug, seen_args = self.main_add('guyzmo/git-repo', 0,
                                             args={'--alone': True})
        assert ('git-repo', 'guyzmo') == repo_slug
        assert {'name': None,
                'alone': True,
                'tracking': 'master'} == seen_args

    def test_add__tracking(self):
        repo_slug, seen_args = self.main_add('guyzmo/git-repo', 0,
                                             args={'--tracking': 'foobar'})
        assert ('git-repo', 'guyzmo') == repo_slug
        assert {'name': None,
                'alone': False,
                'tracking': 'foobar'} == seen_args

    def test_add__tracking_alone(self):
        repo_slug, seen_args = self.main_add('guyzmo/git-repo', 0,
                                             args={'--alone': True,
                                                   '--tracking': 'foobar'})
        assert ('git-repo', 'guyzmo') == repo_slug
        assert {'name': None,
                'alone': True,
                'tracking': 'foobar'} == seen_args

    def test_add__name(self):
        repo_slug, seen_args = self.main_add('guyzmo/git-repo', 0,
                                             args={'<name>': 'foobar'})
        assert ('git-repo', 'guyzmo') == repo_slug
        assert {'name': 'foobar',
                'alone': False,
                'tracking': 'master'} == seen_args

    def test_add__name_tracking(self):
        repo_slug, seen_args = self.main_add('guyzmo/git-repo', 0,
                                             args={'<name>': 'foobar',
                                                   '--tracking': 'barfoo'})
        assert ('git-repo', 'guyzmo') == repo_slug
        assert {'name': 'foobar',
                'alone': False,
                'tracking': 'barfoo'} == seen_args

    def test_add__name_alone(self):
        repo_slug, seen_args = self.main_add('guyzmo/git-repo', 0,
                                             args={'--alone': True,
                                                   '<name>': 'foobar'})
        assert ('git-repo', 'guyzmo') == repo_slug
        assert {'name': 'foobar',
                'alone': True,
                'tracking': 'master'} == seen_args

    def test_add__name_alone_tracking(self):
        repo_slug, seen_args = self.main_add('guyzmo/git-repo', 0,
                                             args={'--alone': True,
                                                   '<name>': 'foobar',
                                                   '--tracking': 'barfoo'})
        assert ('git-repo', 'guyzmo') == repo_slug
        assert {'name': 'foobar',
                'alone': True,
                'tracking': 'barfoo'} == seen_args

    def test_clone(self):
        repo_slug_branch, seen_args = self.main_clone('guyzmo/git-repo', 0)
        assert ('guyzmo', 'git-repo', 'master') == repo_slug_branch

    def test_clone__branch(self):
        repo_slug_branch, seen_args = self.main_clone('guyzmo/git-repo', 0,
                                                      args={'<branch>': 'foobar'})
        assert ('guyzmo', 'git-repo', 'foobar') == repo_slug_branch

    def test_clone__too_many_slashes(self):
        did_clone = self.main_clone('guyzmo/git/repo', 2)
        assert None is did_clone

    def test_create(self):
        repo_slug, seen_args = self.main_create('guyzmo/git-repo', 0)
        assert ('guyzmo', 'git-repo') == repo_slug
        assert {'add': False} == seen_args

    def test_create__add(self):
        repo_slug, seen_args = self.main_create('guyzmo/git-repo', 0, args={'--add': True})
        assert ('guyzmo', 'git-repo') == repo_slug
        assert {'add': True} == seen_args

    def test_create__no_such_path(self):
        did_add = self.main_add('guyzmo/git-repo', 2,
                      {'--path': '/'})
        assert did_add is None

    def test_delete(self):
        repo_slug, seen_args = self.main_delete('guyzmo/git-repo', 0)
        assert ('git-repo', 'guyzmo') == repo_slug
        assert {} == seen_args

    def test_delete__no_user(self):
        repo_slug, seen_args = self.main_delete('git-repo', 0)
        assert ('git-repo',) == repo_slug
        assert {} == seen_args

    def test_fork(self):
        repo_slug, seen_args = self.main_fork('guyzmo/git-repo', 0)
        assert ('guyzmo', 'git-repo') == repo_slug
        assert {'branch': 'master', 'clone': True} == seen_args

    def test_fork__branch(self):
        repo_slug, seen_args = self.main_fork('guyzmo/git-repo', 0,
                                              args={'<branch>': 'foobar'})
        assert ('guyzmo', 'git-repo') == repo_slug
        assert {'branch': 'foobar', 'clone': True} == seen_args

    def test_fork__clone(self):
        repo_slug, seen_args = self.main_fork('guyzmo/git-repo', 0,
                                              args={'--clone': True})
        assert ('guyzmo', 'git-repo') == repo_slug
        assert {'branch': 'master', 'clone': True} == seen_args

    def test_fork__branch_clone(self):
        repo_slug, seen_args = self.main_fork('guyzmo/git-repo', 0,
                                              args={'--clone': True,
                                                    '<branch>': 'foobar'})
        assert ('guyzmo', 'git-repo') == repo_slug
        assert {'branch': 'foobar', 'clone': True} == seen_args

    def test_open(self):
        repo_slug, seen_args = self.main_open('guyzmo/git-repo', 0)
        assert ('guyzmo', 'git-repo') == repo_slug
        assert {} == seen_args

    def test_z_noop(self):
        self.main_noop('guyzmo/git-repo', 1)


