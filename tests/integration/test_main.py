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

    def test_add(self, capsys):
        repo_slug, seen_args = self.main_add('guyzmo/git-repo', 0)
        assert ('git-repo', 'guyzmo') == repo_slug
        assert {'name': None,
                'alone': False,
                'tracking': 'master'} == seen_args
        out, err = capsys.readouterr()
        assert 'Successfully added `guyzmo/git-repo` as remote named `github`\n' == err

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

    def test_add__name(self, capsys):
        repo_slug, seen_args = self.main_add('guyzmo/git-repo', 0,
                                             args={'<name>': 'foobar'})
        assert ('git-repo', 'guyzmo') == repo_slug
        assert {'name': 'foobar',
                'alone': False,
                'tracking': 'master'} == seen_args
        out, err = capsys.readouterr()
        assert 'Successfully added `guyzmo/git-repo` as remote named `foobar`\n' in err

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

    def test_clone__full_url_http(self):
        repo_slug_branch, seen_args = self.main_clone('http://service.com/guyzmo/git-repo', 0)
        assert ('guyzmo', 'git-repo', 'master') == repo_slug_branch

    def test_clone__full_url_https(self):
        repo_slug_branch, seen_args = self.main_clone('https://service.com/guyzmo/git-repo', 0)
        assert ('guyzmo', 'git-repo', 'master') == repo_slug_branch

    def test_clone__full_url_git(self):
        repo_slug_branch, seen_args = self.main_clone('git@service.com/guyzmo/git-repo', 0)
        assert ('guyzmo', 'git-repo', 'master') == repo_slug_branch

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
        repo_slug, seen_args = self.main_delete('guyzmo/git-repo', 0, args={'--force': True})
        assert ('guyzmo', 'git-repo') == repo_slug
        assert {} == seen_args

    def test_delete__ask(self):
        import io, sys
        stdin = sys.stdin
        sys.stdin = io.StringIO('y\nburn!')
        repo_slug, seen_args = self.main_delete('guyzmo/git-repo', 0)
        sys.stdin = stdin
        assert ('guyzmo', 'git-repo') == repo_slug
        assert {} == seen_args

    def test_delete__no_user(self):
        repo_slug, seen_args = self.main_delete('git-repo', 0, args={'--force': True})
        assert ('git-repo',) == repo_slug
        assert {} == seen_args

    def test_fork(self):
        repo_slug, seen_args = self.main_fork('guyzmo/git-repo', 0)
        assert ('guyzmo', 'git-repo') == repo_slug
        assert {} == seen_args

    def test_fork__branch(self):
        repo_slug, seen_args = self.main_fork('guyzmo/git-repo', 0,
                                              args={'<branch>': 'foobar'})
        assert ('guyzmo', 'git-repo') == repo_slug
        assert {} == seen_args

    def test_fork__clone(self):
        repo_slug, seen_args = self.main_fork('guyzmo/git-repo', 0,
                                              args={'--clone': True})
        assert ('guyzmo', 'git-repo') == repo_slug
        assert {} == seen_args

    def test_fork__branch_clone(self):
        repo_slug, seen_args = self.main_fork('guyzmo/git-repo', 0,
                                              args={'--clone': True,
                                                    '<branch>': 'foobar'})
        assert ('guyzmo', 'git-repo') == repo_slug
        assert {} == seen_args

    def test_gist_list(self, capsys, caplog):
        did_list = self.main_gist_list(0, args={})
        out, err = capsys.readouterr()
        assert did_list == ((None,), {})
        assert out ==  ''.join([
            'id1 value1\n',
            'id2 value2\n',
            'id3 value3\n'
            ])

    def test_gist_ls(self, capsys, caplog):
        did_list = self.main_gist_ls(0, args={})
        out, err = capsys.readouterr()
        assert did_list == ((None,), {})
        assert out ==  ''.join([
            'id1 value1\n',
            'id2 value2\n',
            'id3 value3\n'
            ])

    def test_gist_list__with_gist(self, capsys, caplog):
        did_list = self.main_gist_list(0, args={'<gist>': 'foobar'})
        out, err = capsys.readouterr()
        assert did_list == (('foobar',), {})
        assert out ==  ''.join([
            'lang1 size1 name1\n',
            'lang2 size2 name2\n',
            'lang3 size3 name3\n'
            ])

    def test_gist_list__with_bad_gist(self, caplog):
        did_list = self.main_gist_list(2, args={'<gist>': 'bad', '--verbose': 0})
        assert did_list == (('bad',), {})
        assert 'Fatal error: bad gist!' in caplog.text

    def test_gist_clone__with_gist(self, caplog):
        did_clone = self.main_gist_clone(0, args={'<gist>': '42'})
        assert did_clone == (('42',), {})
        assert 'git init' in caplog.text
        assert 'Successfully cloned `42` into `{}/42`!'.format(self.tempdir.name) in caplog.text

    def test_gist_clone__with_bad_gist(self, caplog):
        did_clone = self.main_gist_clone(2, args={'<gist>': 'bad', '--verbose': 0})
        assert did_clone == (('bad',), {})
        assert 'Fatal error: bad gist!\n' in caplog.text

    def test_gist_fetch__with_gist(self, capsys):
        did_fetch = self.main_gist_fetch(0, args={'<gist>': '42'})
        out, err = capsys.readouterr()
        assert did_fetch == (('42', None), {})
        assert out == 'content of a gist\n'
        assert err == ''

    def test_gist_fetch__with_bad_gist(self, caplog):
        did_fetch = self.main_gist_fetch(2, args={'<gist>': 'bad', '--verbose': 0})
        assert did_fetch == (('bad', None), {})
        assert 'Fatal error: bad gist!\n' in caplog.text

    def test_gist_fetch__with_gist_file(self, capsys):
        did_fetch = self.main_gist_fetch(0, args={'<gist>': '42', '<gist_file>': 'fubar'})
        out, err = capsys.readouterr()
        assert did_fetch == (('42', 'fubar'), {})
        assert out == 'content of a gist\n'
        assert err == ''

    def test_gist_fetch__with_bad_gist_file(self, caplog):
        did_fetch = self.main_gist_fetch(2, args={'<gist>': '42', '<gist_file>': 'bad', '--verbose': 0})
        assert did_fetch == (('42', 'bad'), {})
        assert 'Fatal error: bad gist file!\n' in caplog.text

    def test_gist_create(self, caplog):
        did_create = self.main_gist_create(0, args={
            '<gist_path>': ['f1'],
            '<description>': 'fubar',
            '--secret': False,
            '--verbose': 0

        })
        assert did_create == ((['f1'], 'fubar', False), {})
        assert 'Successfully created gist `https://gists/42`!\n' in caplog.text

    def test_gist_create__exists(self, caplog):
        did_create = self.main_gist_create(2, args={
            '<gist_path>': ['exists'],
            '<description>': 'fubar',
            '--secret': False,
            '--verbose': 0
        })
        assert did_create == ((['exists'], 'fubar', False), {})
        assert 'Fatal error: gist exists!' in caplog.text

    def test_gist_create__secret(self, caplog):
        did_create = self.main_gist_create(0, args={
            '<gist_path>': ['f1'],
            '<description>': 'fubar',
            '--secret': True,
            '--verbose': 0

        })
        assert did_create == ((['f1'], 'fubar', True), {})
        assert 'Successfully created gist `https://gists/42`!\n' in caplog.text

    def test_gist_create__secret__exists(self, caplog):
        did_create = self.main_gist_create(2, args={
            '<gist_path>': ['exists'],
            '<description>': 'fubar',
            '--secret': True,
            '--verbose': 0
        })
        assert did_create == ((['exists'], 'fubar', True), {})
        assert 'Fatal error: gist exists!' in caplog.text

    def test_gist_delete__force(self, caplog):
        did_delete = self.main_gist_delete(0, args={'--force': True})
        assert 'Successfully deleted gist!' in caplog.text

    def test_gist_delete__ask(self, caplog):
        import io, sys
        stdin = sys.stdin
        sys.stdin = io.StringIO('y\nburn!')
        did_delete = self.main_gist_delete(0, args={'--force': True})
        sys.stdin = stdin
        assert 'Successfully deleted gist!' in caplog.text

    def test_request_list(self, capsys, caplog):
        from subprocess import call
        call(['git', 'init', '-q', self.tempdir.name])
        repo_slug, seen_args = self.main_request_list('guyzmo/git-repo', 0, args={})
        out, err = capsys.readouterr()
        assert out ==  '1 desc1 http://request/1\n2 desc2 http://request/2\n3 desc3 http://request/3\n'

    def test_request_list__with_repo_slug__no_repo(self, capsys, caplog):
        repo_slug, seen_args = self.main_request_list('guyzmo/git-repo', 0, args={})
        out, err = capsys.readouterr()
        assert out ==  '1 desc1 http://request/1\n2 desc2 http://request/2\n3 desc3 http://request/3\n'

    # Commented out because this does not work on travis CI
    # def test_request_list__no_repo_slug__git(self, capsys, caplog):
    #     from subprocess import call
    #     call(['git', 'init', '-q', self.tempdir.name])
    #     call(['git', '--git-dir={}/.git'.format(self.tempdir.name), 'remote', 'add', 'github', 'https://github.com/guyzmo/git-repo'])
    #     repo_slug, seen_args = self.main_request_list(rc=0, args={})
    #     out, err = capsys.readouterr()
    #     assert ('guyzmo', 'git-repo') == repo_slug
    #     assert dict() == seen_args
    #     assert out ==  '  1\tdesc1                                                       \thttp://request/1\n  2\tdesc2                                                       \thttp://request/2\n  3\tdesc3                                                       \thttp://request/3\n'
    #     assert 'id' in caplog.text and 'title' in caplog.text and 'URL' in caplog.text

    def test_request_list__no_repo_slug__https(self, capsys, caplog):
        from subprocess import call
        call(['git', 'init', '-q', self.tempdir.name])
        call(['git', '--git-dir={}/.git'.format(self.tempdir.name), 'remote', 'add', 'github', 'https://github.com/guyzmo/git-repo'])
        repo_slug, seen_args = self.main_request_list(rc=0, args={})
        assert ('guyzmo', 'git-repo') == repo_slug
        assert dict() == seen_args
        out, err = capsys.readouterr()
        assert out ==  '1 desc1 http://request/1\n2 desc2 http://request/2\n3 desc3 http://request/3\n'

    def test_request_list__no_repo_slug__https_dot_git_fix__issue55(self):
        from subprocess import call
        call(['git', 'init', '-q', self.tempdir.name])
        call(['git', '--git-dir={}/.git'.format(self.tempdir.name), 'remote', 'add', 'github', 'https://github.com/guyzmo/.git-repo'])
        with self.mockup_git('guyzmo', '.git-repo', 'https://github.com/guyzmo/.git-repo'):
            self.set_mock_popen_commands([
                ('git remote get-url --all github', b'https://github.com/guyzmo/.git-repo\n', b'', 0),
            ])
            repo_slug, seen_args = self.main_request_list(rc=0, args={})
            assert ('guyzmo', '.git-repo') == repo_slug
            assert dict() == seen_args

    def test_request_list__no_repo_slug__git_dot_git_fix__issue55(self):
        from subprocess import call
        call(['git', 'init', '-q', self.tempdir.name])
        call(['git', '--git-dir={}/.git'.format(self.tempdir.name), 'remote', 'add', 'github', 'git@github.com:guyzmo/.git-repo'])
        with self.mockup_git('guyzmo', '.git-repo', 'git@github.com:guyzmo/.git-repo'):
            self.set_mock_popen_commands([
                ('git remote get-url --all github', b'git@github.com:guyzmo/.git-repo', b'', 0),
            ])
            repo_slug, seen_args = self.main_request_list(rc=0, args={})
            assert ('guyzmo', '.git-repo') == repo_slug
            assert dict() == seen_args

    def test_request_fetch__request(self, capsys, caplog):
        from subprocess import call
        call(['git', 'init', '-q', self.tempdir.name])
        seen_args, extra_args = self.main_request_fetch('guyzmo/git-repo', 0,
                args={'<request>': '42'})
        out, err = capsys.readouterr()
        assert ('guyzmo', 'git-repo', '42') == seen_args
        assert {'force': False} == extra_args
        assert out == ''
        assert 'Successfully fetched request id `42` of `guyzmo/git-repo` into `pr/42`!' in caplog.text

    # Commented out because this does not work on travis CI
    # def test_request_fetch__request__no_repo_slug__git(self, capsys, caplog):
    #     from subprocess import call
    #     call(['git', 'init', '-q', self.tempdir.name])
    #     call(['git', '--git-dir={}/.git'.format(self.tempdir.name), 'remote', 'add', 'github', 'https://github.com/guyzmo/git-repo'])
    #     seen_args, extra_args = self.main_request_fetch(rc=0, args={'<request>': '42'})
    #     out, err = capsys.readouterr()
    #     assert ('guyzmo', 'git-repo', '42') == seen_args
    #     assert {'force': False} == extra_args
    #     assert out == ''
    #     assert 'Successfully fetched request id `42` of `guyzmo/git-repo` into `pr/42`!' in caplog.text

    def test_request_fetch__request__no_repo_slug__https(self, capsys, caplog):
        from subprocess import call
        call(['git', 'init', '-q', self.tempdir.name])
        call(['git', '--git-dir={}/.git'.format(self.tempdir.name), 'remote', 'add', 'github', 'https://github.com/guyzmo/git-repo'])
        seen_args, extra_args = self.main_request_fetch(rc=0, args={'<request>': '42'})
        out, err = capsys.readouterr()
        assert ('guyzmo', 'git-repo', '42') == seen_args
        assert {'force': False} == extra_args
        assert out == ''
        assert 'Successfully fetched request id `42` of `guyzmo/git-repo` into `pr/42`!' in caplog.text

    def test_request_fetch__bad_request(self, capsys, caplog):
        from subprocess import call
        call(['git', 'init', '-q', self.tempdir.name])
        seen_args, extra_args = self.main_request_fetch('guyzmo/git-repo', 2,
                args={'<request>': 'bad', '--verbose': 0})
        out, err = capsys.readouterr()
        assert ('guyzmo', 'git-repo', 'bad') == seen_args
        assert {'force': False} == extra_args
        assert out == ''
        assert 'Fatal error: bad request for merge!' in caplog.text

    def test_request_create(self, capsys, caplog):
        from subprocess import call
        call(['git', 'init', '-q', self.tempdir.name])
        seen_args, extra_args = self.main_request_create('guyzmo/test', 0,
                args={
                    '<local_branch>': 'pr-test',
                    '<remote_branch>': 'base-test',
                    '<title>': 'This is a test',
                    '--message': 'This is a test'
                    })
        out, err = capsys.readouterr()
        seen_args = seen_args[:-1] # remove the passed edition function
        assert ('guyzmo', 'test', 'pr-test', 'base-test', 'This is a test', 'This is a test', True) == seen_args
        assert {} == extra_args
        assert out == ''
        assert 'Successfully created request of `pr-test` onto `guyzmo/test:base-test`, with id `42`!' in caplog.text

    def test_request_create__no_description(self, capsys, caplog):
        from subprocess import call
        call(['git', 'init', '-q', self.tempdir.name])
        seen_args, extra_args = self.main_request_create('guyzmo/test', 0,
                args={
                    '<local_branch>': 'pr-test',
                    '<remote_branch>': 'base-test',
                    '<title>': 'This is a test',
                    })
        out, err = capsys.readouterr()
        seen_args = seen_args[:-1] # remove the passed edition function
        assert ('guyzmo', 'test', 'pr-test', 'base-test', 'This is a test', None, True) == seen_args
        assert {} == extra_args
        assert out == ''
        assert 'Successfully created request of `pr-test` onto `guyzmo/test:base-test`, with id `42`!' in caplog.text

    def test_request_create__bad_local_branch(self, capsys, caplog):
        from subprocess import call
        call(['git', 'init', '-q', self.tempdir.name])
        seen_args, extra_args = self.main_request_create('guyzmo/test', 2,
                args={
                    '<local_branch>': 'bad',
                    '<remote_branch>': 'base-test',
                    '<title>': 'This is a test',
                    '--message': 'This is a test'
                    })
        out, err = capsys.readouterr()
        seen_args = seen_args[:-1] # remove the passed edition function
        assert ('guyzmo', 'test', 'bad', 'base-test', 'This is a test', 'This is a test', True) == seen_args
        assert {} == extra_args
        assert out == ''
        assert 'Fatal error: bad branch to request!' in caplog.text

    def test_request_create__bad_remote_branch(self, capsys, caplog):
        from subprocess import call
        call(['git', 'init', '-q', self.tempdir.name])
        seen_args, extra_args = self.main_request_create('guyzmo/test', 2,
                args={
                    '<local_branch>': 'pr-test',
                    '<remote_branch>': 'bad',
                    '<title>': 'This is a test',
                    '--message': 'This is a test'
                    })
        out, err = capsys.readouterr()
        seen_args = seen_args[:-1] # remove the passed edition function
        assert ('guyzmo', 'test', 'pr-test', 'bad', 'This is a test', 'This is a test', True) == seen_args
        assert {} == extra_args
        assert out == ''
        assert 'Fatal error: bad branch to request!' in caplog.text

    def test_request_create__no_local_branch(self, capsys, caplog):
        from subprocess import call
        call(['git', 'init', '-q', self.tempdir.name])
        seen_args, extra_args = self.main_request_create('guyzmo/test', 0,
                args={
                    '<remote_branch>': 'base-test',
                    '<title>': 'This is a test',
                    '--message': 'This is a test'
                    })
        out, err = capsys.readouterr()
        seen_args = seen_args[:-1] # remove the passed edition function
        assert ('guyzmo', 'test', None, 'base-test', 'This is a test', 'This is a test', True) == seen_args
        assert {} == extra_args
        assert out == ''
        assert 'Successfully created request of `pr-test` onto `guyzmo/test:base-test`, with id `42`!' in caplog.text

    def test_request_create__no_remote_branch(self, capsys, caplog):
        from subprocess import call
        call(['git', 'init', '-q', self.tempdir.name])
        seen_args, extra_args = self.main_request_create('guyzmo/test', 0,
                args={
                    '<local_branch>': 'pr-test',
                    '<title>': 'This is a test',
                    '--message': 'This is a test'
                    })
        out, err = capsys.readouterr()
        seen_args = seen_args[:-1] # remove the passed edition function
        assert ('guyzmo', 'test', 'pr-test', None, 'This is a test', 'This is a test', True) == seen_args
        assert {} == extra_args
        assert out == ''
        assert 'Successfully created request of `pr-test` onto `guyzmo/test:base-test`, with id `42`!' in caplog.text

    def test_open(self):
        repo_slug, seen_args = self.main_open('guyzmo/git-repo', 0)
        assert ('guyzmo', 'git-repo') == repo_slug
        assert {} == seen_args

    def _create_repository(self, ro=False):
        from subprocess import call
        call(['git', 'init', '-q', self.tempdir.name])
        if ro:
            call(['git','--git-dir={}/.git'.format(self.tempdir.name), 'remote', 'add', 'github', 'https://github.com/guyzmo/git-repo'])
        else:
            call(['git','--git-dir={}/.git'.format(self.tempdir.name), 'remote', 'add', 'github', 'git@github.com:guyzmo/git-repo'])

    def test_open__no_repo_slug__https(self):
        self._create_repository(ro=True)
        repo_slug, seen_args = self.main_open(rc=0)
        assert ('guyzmo', 'git-repo') == repo_slug
        assert {} == seen_args

    # Commented out because this does not work on travis CI
    # def test_open__no_repo_slug__git(self):
    #     self._create_repository()
    #     repo_slug, seen_args = self.main_open(rc=0)
    #     assert ('guyzmo', 'git-repo') == repo_slug
    #     assert {} == seen_args

    def test_create__no_repo_slug(self):
        self._create_repository(ro=True)
        repo_slug, seen_args = self.main_create(rc=0)
        assert ('guyzmo', 'git-repo') == repo_slug
        assert {'add': False} == seen_args

    def test_fork__no_repo_slug(self):
        self._create_repository(ro=True)
        repo_slug, seen_args = self.main_fork(rc=0)
        assert ('guyzmo', 'git-repo') == repo_slug
        assert {} == seen_args

    def test_delete__no_repo_slug(self):
        self._create_repository(ro=True)
        repo_slug, seen_args = self.main_delete(rc=0, args={'--force': True})
        assert ('guyzmo', 'git-repo') == repo_slug
        assert {} == seen_args

    def test_request_list__no_repo_slug(self, capsys, caplog):
        self._create_repository(ro=True)
        repo_slug, seen_args = self.main_request_list(rc=0, args={})
        out, err = capsys.readouterr()
        assert out ==  '1 desc1 http://request/1\n2 desc2 http://request/2\n3 desc3 http://request/3\n'

    def test_request_fetch__no_repo_slug(self, capsys, caplog):
        self._create_repository(ro=True)
        seen_args, extra_args = self.main_request_fetch(rc=0,
                args={'<request>': '42'})
        out, err = capsys.readouterr()
        assert ('guyzmo', 'git-repo', '42') == seen_args
        assert {'force': False} == extra_args
        assert out == ''
        assert 'Successfully fetched request id `42` of `guyzmo/git-repo` into `pr/42`!' in caplog.text

    def test_request_create__no_repo_slug(self, capsys, caplog):
        self._create_repository(ro=True)
        seen_args, extra_args = self.main_request_create(rc=0,
                args={
                    '<local_branch>': 'pr-test',
                    '<remote_branch>': 'base-test',
                    '<title>': 'This is a test',
                    '--message': 'This is a test'
                    })
        out, err = capsys.readouterr()
        seen_args = seen_args[:-1] # remove the passed edition function
        assert ('guyzmo', 'git-repo', 'pr-test', 'base-test', 'This is a test', 'This is a test', True) == seen_args
        assert {} == extra_args
        assert out == ''
        assert 'Successfully created request of `pr-test` onto `guyzmo/git-repo:base-test`, with id `42`!' in caplog.text

    def test_config(self, capsys, caplog):
        import sys, io, getpass
        getpass.getpass = input
        sys.stdin = io.StringIO('\n'.join(['y', 'n', 'user', 'pass', 'y', 'fubar', 'y']))
        #
        conf = self.main_config(target='hub', rc=0)
        assert sorted(['[gitrepo "github"]\n',
                '\tremote = fubar\n',
                '\ttoken = user:pass\n',
                '[alias]\n',
                '\ttest_command = repo test_command\n']) == sorted(conf)
        last_conf = conf

        sys.stdin = io.StringIO('\n'.join([
            'y', 'y', 'frama', 'framagit.org', '', '', '', '', 'user', 'pass', 'y', 'framagit', 'y']))
        #
        conf = self.main_config(target='lab', rc=0)
        assert sorted(last_conf+[
                '[gitrepo "frama"]\n',
                '\tfqdn = framagit.org\n',
                '\tremote = framagit\n',
                '\ttype = gitlab\n',
                '\tname = frama\n',
                '\tcommand = frama\n',
                '\tport = 443\n',
                '\tscheme = https\n',
                '\tinsecure = False\n',
                '\ttoken = user:pass\n', ]) == sorted(conf)
        last_conf = conf

        sys.stdin = io.StringIO('\n'.join([
            'y', 'y', 'test0r', 'localhost', '8080', 'n', 'user', 'pass', 'y', 'test', 'y']))
        #
        conf = self.main_config(target='lab', rc=0)
        assert sorted(last_conf+[
                '[gitrepo "test0r"]\n',
                '\tfqdn = localhost\n',
                '\tremote = test\n',
                '\ttype = gitlab\n',
                '\tname = test0r\n',
                '\tcommand = test0r\n',
                '\tport = 8080\n',
                '\tscheme = http\n',
                '\ttoken = user:pass\n', ]) == sorted(conf)
        last_conf = conf

        sys.stdin = io.StringIO('\n'.join([
            'y', 'y', 'selfsigned', 'server.local', '8443',
            '', '', 'y', '/etc/server.pem', 'user', 'pass', 'y', 'self', 'y']))
        #
        conf = self.main_config(target='lab', rc=0)
        assert sorted(last_conf+['[gitrepo "selfsigned"]\n',
                '\tfqdn = server.local\n',
                '\tremote = self\n',
                '\ttype = gitlab\n',
                '\tname = selfsigned\n',
                '\tcommand = selfsigned\n',
                '\tport = 8443\n',
                '\tscheme = https\n',
                '\tinsecure = False\n',
                '\tserver-cert = /etc/server.pem\n',
                '\ttoken = user:pass\n', ]) == sorted(conf)
        last_conf = conf

        sys.stdin = io.StringIO('\n'.join([
            'y', 'y', 'lamer', 'pwnme.com', '',
            '', 'y', 'user', 'pass', 'y', 'l', 'y']))
        #
        conf = self.main_config(target='lab', rc=0)
        assert sorted(last_conf+['[gitrepo "lamer"]\n',
                '\tfqdn = pwnme.com\n',
                '\tremote = l\n',
                '\ttype = gitlab\n',
                '\tname = lamer\n',
                '\tcommand = lamer\n',
                '\tport = 443\n',
                '\tscheme = https\n',
                '\tinsecure = True\n',
                '\ttoken = user:pass\n', ]) == sorted(conf)

    def test_z_noop(self):
        self.main_noop('guyzmo/git-repo', 1)

