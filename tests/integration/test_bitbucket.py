#!/usr/bin/env python3

import logging

#################################################################################
# Enable logging

log = logging.getLogger('test.bitbucket')

#################################################################################

import os
import sys
import pytest

from tests.helpers import GitRepoTestCase

from git_repo.services.service import bitbucket
from git_repo.exceptions import ResourceNotFoundError, ResourceError

class Test_BitBucket(GitRepoTestCase):
    log = log

    @property
    def local_namespace(self):
        if 'BITBUCKET_NAMESPACE' in os.environ:
            return os.environ['BITBUCKET_NAMESPACE']
        return 'git-repo-test'

    def get_service(self):
        service = bitbucket.BitbucketService(c=dict())
        return service

    def get_requests_session(self):
        return self.service.bb.client.session

    def test_00_fork(self):
        self.action_fork(local_namespace=self.local_namespace,
                        remote_namespace='abdo2015',
                        repository='git_tutorial')

    def test_01_create(self):
        self.action_create(namespace=self.local_namespace,
                           repository='foobar')


    def test_02_delete(self):
        self.action_delete(namespace=self.local_namespace,
                           repository='foobar')

    def test_03_delete_nouser(self):
        self.action_delete(repository='git_tutorial')

    def test_04_clone(self):
        self.action_clone(namespace='guyzmo',
                          repository='git-repo')

    def test_05_add(self):
        self.action_add(namespace='guyzmo',
                        repository='git-repo')

    def test_06_add__name(self):
        self.action_add(namespace='guyzmo',
                        repository='git-repo',
                        name='test0r')

    def test_07_add__alone(self):
        self.action_add(namespace='guyzmo',
                        repository='git-repo',
                        alone=True)

    def test_08_add__alone_name(self):
        self.action_add(namespace='guyzmo',
                        repository='git-repo',
                        name='test0r',
                        alone=True)

    def test_09_add__default(self):
        self.action_add(namespace='guyzmo',
                        repository='git-repo',
                        tracking='bitbucket')

    def test_10_add__default_name(self):
        self.action_add(namespace='guyzmo',
                        repository='git-repo',
                        name='test0r',
                        tracking='bitbucket')

    def test_11_add__alone_default(self):
        self.action_add(namespace='guyzmo',
                        repository='git-repo',
                        alone=True,
                        tracking='bitbucket')

    def test_12_add__alone_default_name(self):
        self.action_add(namespace='guyzmo',
                        repository='git-repo',
                        alone=True,
                        name='test0r',
                        tracking='bitbucket')

    def test_13_snippet_list(self):
        s_list = [
            ('https://bitbucket.org/snippets/guyzmo/ggd4X', 'test'),
            ('https://bitbucket.org/snippets/guyzmo/ggda9', 'test2'),
            ('https://bitbucket.org/snippets/guyzmo/77gaA', 'test3'),
        ]
        self.action_gist_list(gist_list_data=s_list)

    def test_14_snippet_list_with_gist(self):
        g_list = [
            'N.A.                  0 aoeu1.txt',
            'N.A.                  0 aeou2.txt',
        ]
        self.action_gist_list(gist='ggd4X')

    def test_15_snippet_list_with_bad_gist(self):
        with pytest.raises(ResourceNotFoundError):
            self.action_gist_list(gist='42')

    def test_16_snippet_clone_with_gist(self):
        self.action_gist_clone(
            gist='https://bitbucket.org/snippets/{}/ggd4X'.format(os.environ.get('BITBUCKET_NAMESPACE', 'error')),
            clone_url='ssh://git@bitbucket.org/snippets/{}/ggd4X/test'.format(os.environ.get('BITBUCKET_NAMESPACE', 'error'))
        )

    def test_17_snippet_fetch_with_gist(self):
        content = self.action_gist_fetch(gist='77gaA', gist_file=None)
        assert content == '\n'.join([ 'ttt' ])

    def test_18_snippet_fetch_with_bad_gist(self):
        with pytest.raises(ResourceNotFoundError):
            self.action_gist_fetch(gist='69', gist_file=None)

    def test_19_snippet_fetch_with_gist_file(self):
        content = self.action_gist_fetch(gist='ggd4X', gist_file='aoeu1.txt')
        assert content == '\n'.join([ '1' ])

    def test_20_snippet_fetch_with_bad_gist_file(self):
        with pytest.raises(ResourceNotFoundError):
            self.action_gist_fetch(gist='ggd4X', gist_file='failed')

    def test_21_snippet_create_gist_file(self, datadir):
        test_file = str(datadir[ 'random-fortune-1.txt' ])
        self.action_gist_create(description='this is a test.',
                gist_files=[ test_file ],
                secret=False)

    def test_22_snippet_create_gist_file_list(self, datadir):
        test_files = [
                str(datadir[ 'random-fortune-1.txt' ]),
                str(datadir[ 'random-fortune-2.txt' ]),
                str(datadir[ 'random-fortune-3.txt' ]),
                str(datadir[ 'random-fortune-4.txt' ]),
        ]
        self.action_gist_create(description='this is a test.',
                gist_files=test_files,
                secret=False)

    def test_23_snippet_create_gist_dir(self, datadir):
        test_dir = [
                str(datadir[ 'a_directory' ]),
        ]
        self.action_gist_create(description='this is a test.',
                gist_files=test_dir,
                secret=False)

    def test_24_snippet_create_gist_file(self, datadir):
        test_file = str(datadir[ 'random-fortune-1.txt' ])
        self.action_gist_create(description='this is a secret test.',
                gist_files=[ test_file ],
                secret=True)

    def test_25_snippet_create_gist_file_list(self, datadir):
        test_files = [
                str(datadir[ 'random-fortune-1.txt' ]),
                str(datadir[ 'random-fortune-2.txt' ]),
                str(datadir[ 'random-fortune-3.txt' ]),
                str(datadir[ 'random-fortune-4.txt' ]),
        ]
        self.action_gist_create(description='this is a secret test.',
                gist_files=test_files,
                secret=True)

    def test_26_snippet_create_gist_dir(self, datadir):
        test_dir = [
                str(datadir[ 'a_directory' ]),
        ]
        self.action_gist_create(description='this is a secret test.',
                gist_files=test_dir,
                secret=True)

    def test_27_snippet_delete(self):
        self.action_gist_delete(gist='p4RzX')

    def test_28_snippet_delete__not_exist(self):
        with pytest.raises(ResourceNotFoundError):
            self.action_gist_delete(gist='p4RzX')

    def test_29_snippet_create_snippet__file_not_exist(self, datadir):
        with pytest.raises(FileNotFoundError):
            test_dir = [
                    'does_not_exists'
            ]
            self.action_gist_create(description='this is a secret test.',
                    gist_files=test_dir,
                    secret=False)

    def test_30_request_list(self):
        self.action_request_list(
                namespace='atlassian',
                repository='python-bitbucket',
                rq_list_data=[
            ('1', 'Bugfixes for two crashes appearing during reply parsing of repository_create (output of this command is different from normal status, unfortunately). The latter appeared after I fixed the former.', 'https://bitbucket.org/atlassian/python-bitbucket/pull-requests/1'),
            ('2', 'Attempt to fix bitbucket_create crash again, this time py3k compatible', 'https://bitbucket.org/atlassian/python-bitbucket/pull-requests/2'),
            ('3', '[WIP] Initial support for webhooks', 'https://bitbucket.org/atlassian/python-bitbucket/pull-requests/3'),
            ('4', 'fix: lookups for PRs based on state were calling a non existant method', 'https://bitbucket.org/atlassian/python-bitbucket/pull-requests/4'),
            ('5', '🚧 Fork feature implementation', 'https://bitbucket.org/atlassian/python-bitbucket/pull-requests/5'),
            ('6', '💄 Updated code style to be closer to python3 style', 'https://bitbucket.org/atlassian/python-bitbucket/pull-requests/6'),
        ])

    def test_30_request_list_empty(self):
        self.action_request_list(
                namespace='guyzmo',
                repository='git-repo',
                rq_list_data=[ ])

    def test_31_request_fetch__good(self):
        namespace='atlassian'
        repository='python-bitbucket'
        request='2'
        local_branch='requests/bitbucket'
        local_slug = self.service.format_path(namespace=namespace, repository=repository, rw=False)
        remote_branch='repo_create_bugfix_again'
        remote_name='requests-bitbucket-Mekk-python-bitbucket'
        with self.recorder.use_cassette(self._make_cassette_name(1)):
            with self.mockup_git(namespace, repository):
                self.set_mock_popen_commands([
                    ('git remote add all {}'.format(local_slug), b'', b'', 0),
                    ('git remote add {} {}'.format(self.service.name, local_slug), b'', b'', 0),
                    ('git remote add requests-bitbucket-Mekk-python-bitbucket https://bitbucket.org/Mekk/python-bitbucket', b'', b'', 0),
                    ('git version', b'git version 2.8.0', b'', 0),
                    ('git pull --progress -v {} master'.format(self.service.name), b'', '\n'.join([
                        'POST git-upload-pack (140 bytes)',
                        'remote: Counting objects: 8318, done.',
                        'remote: Compressing objects: 100% (3/3), done.',
                        'remote: Total 8318 (delta 0), reused 0 (delta 0), pack-reused 8315',
                        'Receiving objects: 100% (8318/8318), 3.59 MiB | 974.00 KiB/s, done.',
                        'Resolving deltas: 100% (5126/5126), done.',
                        'From {}:{}/{}'.format(self.service.fqdn, namespace, repository),
                        ' * branch            master     -> FETCH_HEAD',
                        ' * [new branch]      master     -> {1}/{0}'.format(request, local_branch)]).encode('utf-8'),
                    0),
                    ('git fetch --progress -v {0} {2}/{1}/head:{3}/{1}'.format(
                            self.service.name,
                            request,
                            remote_branch,
                            local_branch), b'', '\n'.join([
                        'POST git-upload-pack (140 bytes)',
                        'remote: Counting objects: 8318, done.',
                        'remote: Compressing objects: 100% (3/3), done.',
                        'remote: Total 8318 (delta 0), reused 0 (delta 0), pack-reused 8315',
                        'Receiving objects: 100% (8318/8318), 3.59 MiB | 974.00 KiB/s, done.',
                        'Resolving deltas: 100% (5126/5126), done.',
                        'From {}:{}/{}'.format(self.service.fqdn, namespace, repository),
                        ' * [new branch]      master     -> request/{}'.format(request)]).encode('utf-8'),
                    0),
                    ('git fetch --progress -v {} {}:{}/{}'.format(
                            remote_name,
                            remote_branch,
                            local_branch, request), b'', '\n'.join([
                        'POST git-upload-pack (140 bytes)',
                        'remote: Counting objects: 8318, done.',
                        'remote: Compressing objects: 100% (3/3), done.',
                        'remote: Total 8318 (delta 0), reused 0 (delta 0), pack-reused 8315',
                        'Receiving objects: 100% (8318/8318), 3.59 MiB | 974.00 KiB/s, done.',
                        'Resolving deltas: 100% (5126/5126), done.',
                        'From {}:{}/{}'.format(self.service.fqdn, namespace, repository),
                        ' * [new branch]      {}     -> {}/{}'.format(remote_branch, local_branch, request),
                        ' * [new branch]      {}     -> {}/{}'.format(remote_branch, remote_name, remote_branch),
                        ]).encode('utf-8'),
                    0)
                    ])
                self.service.connect()
                self.service.clone(namespace, repository, rw=False)
                self.service.repository.create_remote('all', url=local_slug)
                self.service.repository.create_remote(self.service.name, url=local_slug)
                self.service.request_fetch(repo=repository, user=namespace, request=request)

    @pytest.mark.skip
    # Skipping this test because of bug in gitpython, cf https://github.com/gitpython-developers/gitpython#:
    #   > Pumping 'stderr' of cmd(['git', 'pull', '--progress', '-v', 'bitbucket', 'master']) failed due to: TypeError("a bytes-like object is required, not 'str'",)
    #   Exception in thread Thread-10:
    #   Traceback (most recent call last):
    #     File "/home/travis/virtualenv/python3.6.1/lib/python3.6/site-packages/git/cmd.py", line 87, in pump_stream
    #       handler(line)
    #     File "/home/travis/virtualenv/python3.6.1/lib/python3.6/site-packages/git/util.py", line 483, in handler
    #       return self._parse_progress_line(line.rstrip())
    #     File "/home/travis/virtualenv/python3.6.1/lib/python3.6/site-packages/git/util.py", line 388, in _parse_progress_line
    #       if len(self.error_lines) > 0 or self._cur_line.startswith(('error:', 'fatal:')):
    #   TypeError: a bytes-like object is required, not 'str'
    #   During handling of the above exception, another exception occurred:
    #   Traceback (most recent call last):
    #     File "/opt/python/3.6.1/lib/python3.6/threading.py", line 916, in _bootstrap_inner
    #       self.run()
    #     File "/opt/python/3.6.1/lib/python3.6/threading.py", line 864, in run
    #       self._target(*self._args, **self._kwargs)
    #     File "/home/travis/virtualenv/python3.6.1/lib/python3.6/site-packages/git/cmd.py", line 90, in pump_stream
    #       raise CommandError(['<%s-pump>' % name] + cmdline, ex)
    #   git.exc.CommandError: Cmd('<stderr-pump>') failed due to: TypeError('a bytes-like object is required, not 'str'')
    #     cmdline: <stderr-pump> git pull --progress -v bitbucket master
    def test_31_request_fetch__bad_request(self):
        with pytest.raises(ResourceNotFoundError):
            self.action_request_fetch(namespace='atlassian',
                repository='python-bitbucket',
                request='42',
                fail=True)

    def test_32_request_create__good(self):
        r = self.action_request_create(namespace=self.local_namespace,
                repository='test_create_requests',
                target_branch='master',
                source_branch='pr-test',
                title='PR test',
                description='PR description',
                expected_result=[
                    '{}',
                     ['Successfully created request of `pr-test` onto `_namespace_bitbucket_/test_create_requests:master, with id `1'],
                     ['available at https://bitbucket.org/_namespace_bitbucket_/test_create_requests/pull-requests/1']
        ])

    def test_32_request_create__bad_branch(self):
        with pytest.raises(ResourceNotFoundError):
            self.action_request_create(namespace=self.local_namespace,
                    repository='test_create_requests',
                    target_branch='master',
                    source_branch='does_not_exists',
                    title='PR test',
                    description='PR description')

    def test_32_request_create__bad_repo(self):
        with pytest.raises(ResourceNotFoundError):
            r = self.action_request_create(namespace=self.local_namespace,
                    repository='does_not_exists',
                    target_branch='master',
                    source_branch='pr-test',
                    title='PR test',
                    description='PR description')

    @pytest.mark.skip
    # will need cassette regeneration
    def test_32_request_create__guess_branch(self):
        r = self.action_request_create(namespace=self.local_namespace,
                repository='test_create_requests',
                target_branch=None,
                source_branch=None,
                title='PR test',
                description='PR description',
                expected_result=[
                    '{}',
                     ['Successfully created request of `pr-test` onto `_namespace_bitbucket_/test_create_requests:master, with id `1'],
                     ['available at https://bitbucket.org/_namespace_bitbucket_/test_create_requests/pull-requests/1']
        ])

    def test_33_open(self):
        self.action_open(namespace='guyzmo',
                         repository='git-repo')

    def test_34_list__short(self, caplog):
        projects = self.action_list(namespace='git-repo-test')
        assert projects == ['{}', ('Total repositories: 1',), ['git-repo-test/git-repo']]
        assert 'GET /2.0/users/git-repo-test' in caplog.text
        assert 'GET /2.0/repositories/git-repo-test HTTP/1.1' in caplog.text

    def test_34_list__long(self, caplog):
        projects = self.action_list(namespace='git-repo-test', _long=True)
        assert projects == ['{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{:12}\t{}',
                ['Status', 'Commits', 'Reqs', 'Issues', 'Forks', 'Coders', 'Watch', 'Likes', 'Lang', 'Modif', 'Name'],
                ['F ', '92', '1', 'N.A.', '1', 'N.A.', '1', 'N.A.', 'python', '2016-03-30T13:30:15.637449+00:00', 'git-repo-test/git-repo']]
        assert 'GET /2.0/users/git-repo-test' in caplog.text
        assert 'GET /2.0/repositories/git-repo-test HTTP/1.1' in caplog.text


