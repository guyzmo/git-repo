#!/usr/bin/env python

import os
import tempfile
import unittest

#################################################################################
# make all debug prefix more readable by colourising them

fmt = dict(
    green = '[32m',
    red = '[31m',
    blue = '[35m',
    magenta = '[34m',
    cyan = '[96m',
    reset = '[0m'
)
def colour_name(logger, colour):
    if not 'git_repo' in logger.name:
        logger.name = 'git_repo.{}'.format(logger.name)
    format_name = '{'+colour+'}{}{reset}'
    logger.name = format_name.format(logger.name, **fmt)

from github3.session import __logs__ as gh3_log
colour_name(gh3_log, 'cyan')

from git.cmd import log as git_log
colour_name(git_log, 'magenta')

from git_repo.repo import log as gr_log
colour_name(gr_log, 'green')

from git_repo.services.github import log as ggh_log
colour_name(ggh_log, 'blue')

#################################################################################

import logging
log = logging.getLogger('{red}test.github{reset}'.format(**fmt))

from git_repo.repo import main  #services.base import RepositoryService

class TestCase(unittest.TestCase):
    target = ''

    def setUp(self):
        log.info(__name__)
        self.tempdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        log.info(__name__)
        self.tempdir.cleanup()

    def setup_args(self, d):
        cli_args = {
            '--force': False,
            '--help': False,
            '--path': '.',
            '--verbose': 4,
            '<branch>': None,
            '<target>': self.target,
            '<user>/<repo>': '',
            'add': False,
            'clone': False,
            'create': False,
            'delete': False,
            'fork': False,
            'open': False
        }
        cli_args.update(d)
        return cli_args

    def api_clone(self, repo, rc=0):
        log.info(__name__)
        assert rc == main(self.setup_args({
            'clone': True,
            '<user>/<repo>': repo,
            '--path': self.tempdir.name
        })), "Non {} result for clone".format(rc)

    def api_fork(self, repo, rc=0):
        log.info(__name__)
        assert rc == main(self.setup_args({
            'fork': True,
            '<user>/<repo>': repo,
            '--path': self.tempdir.name
        })), "Non {} result for fork".format(rc)

    def api_create(self, repo, rc=0):
        log.info(__name__)
        assert rc == main(self.setup_args({
            'create': True,
            '<user>/<repo>': repo,
            '--path': self.tempdir.name
        })), "Non {} result for create".format(rc)

    def api_delete(self, repo, rc=0):
        log.info(__name__)
        assert rc == main(self.setup_args({
            'delete': True,
            '<user>/<repo>': repo,
            '--force': True,
            '--path': self.tempdir.name,
        })), "Non {} result for delete".format(rc)

    def api_add(self, repo, rc=0):
        log.info(__name__)
        assert rc == main(self.setup_args({
            'add': True,
            '<user>/<repo>': repo,
            '--path': self.tempdir.name
        })), "Non {} result for add".format(rc)

    def api_open(self, repo, rc=0):
        log.info(__name__)
        assert rc == main(self.setup_args({
            'open': True,
            '<user>/<repo>': repo,
            '--path': self.tempdir.name
        })), "Non {} result for open".format(rc)

    def api_noop(self, repo, rc=1):
        log.info(__name__)
        assert rc == main(self.setup_args({
            '<user>/<repo>': repo,
            '--path': self.tempdir.name
        })), "Non {} result for no-action".format(rc)
