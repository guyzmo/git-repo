#!/usr/bin/env python3
# encoding: utf-8
from setuptools import setup, find_packages

import sys, os

import pip

from setuptools import setup, find_packages, dist
from setuptools.command.test import test as TestCommand
from distutils.core import Command
from distutils.core import setup

if sys.version_info.major < 3:
    print('Please install with python version 3')
    sys.exit(1)

class DistClean(Command):
    description = 'Clean the repository from all buildout stuff'
    user_options = []

    def initialize_options(self): pass
    def finalize_options(self): pass

    def run(self):
        import shutil, os
        from glob import glob
        path = os.path.split(__file__)[0]
        shutil.rmtree(os.path.join(path, 'var'), ignore_errors=True)
        shutil.rmtree(os.path.join(path, 'bin'), ignore_errors=True)
        shutil.rmtree(os.path.join(path, '.tox'), ignore_errors=True)
        for fname in glob('*.egg-info'):
            shutil.rmtree(os.path.join(path, fname), ignore_errors=True)
        shutil.rmtree(os.path.join(path, '.eggs'), ignore_errors=True)
        shutil.rmtree(os.path.join(path, 'build'), ignore_errors=True)
        shutil.rmtree(os.path.join(path, 'dist'), ignore_errors=True)
        shutil.rmtree(os.path.join(path, '.installed.cfg'), ignore_errors=True)
        print("Repository is now clean!")


class PyTest(TestCommand):
    user_options = [
            ('exitfirst', 'x', "exit instantly on first error or failed test."),
            ('last-failed', 'l', "rerun only the tests that failed at the last run"),
            ('verbose', 'v', "increase verbosity"),
            ('pdb', 'p', "run pdb upon failure"),
            ('pep8', '8', "perform some pep8 sanity checks on .py files"),
            ('flakes', 'f', "run flakes on .py files"),
            ('pytest-args=', 'a', "Extra arguments to pass into py.test"),
            ]
    default_options = [
        '--cov=calenvite', '--cov-report', 'term-missing',
        '--capture=sys', 'tests'
    ]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = set()
        self.exitfirst = False
        self.last_failed = False
        self.verbose = 0
        self.pdb = False
        self.pep8 = False
        self.flakes = False

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        if isinstance(self.pytest_args, str):
            self.pytest_args = set(self.pytest_args.split(' '))
        if self.exitfirst:   self.pytest_args.add('-x')
        if self.pdb:   self.pytest_args.add('--pdb')
        if self.last_failed: self.pytest_args.add('--last-failed')
        if self.pep8:        self.pytest_args.add('--pep8')
        if self.flakes:      self.pytest_args.add('--flakes')
        self.pytest_args = list(self.pytest_args)
        if self.verbose:
            for v in range(self.verbose):
                self.pytest_args.append('-v')
        errno = pytest.main(self.pytest_args + self.default_options)
        sys.exit(errno)


requirements = [
    'docopt',
    'progress',
    'python-dateutil',
    'lxml',
    'GitPython',
    'github3.py<1.0.0',
    'python-gitlab',
    'gogs-client',
    'pybitbucket_fork',
    'python-gerritclient',
]

requirements_tests = [
    'pytest',
    'pytest-cov',
    'pytest-sugar',
    'pytest-catchlog',
    'pytest-datadir-ng',
    'testfixtures',
    'mock',
    'betamax==0.5.1',
    'betamax-serializers',
]

requirements_links = []

setup(name='git-repo',
      description='Tool for managing repository services from your git CLI tool',
      classifiers=[
          # 'Development Status :: 2 - Pre-Alpha',
          # 'Development Status :: 3 - Alpha',
          'Development Status :: 4 - Beta',
          # 'Development Status :: 5 - Production/Stable',
          # 'Development Status :: 6 - Mature',
          # 'Development Status :: 7 - Inactive',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Topic :: Software Development',
          'Topic :: Software Development :: Version Control',
          'Topic :: Utilities',
      ],
      keywords='git',
      url='https://github.com/guyzmo/git-repo',
      author='Bernard `Guyzmo` Pratz',
      author_email='guyzmo+git-repo@m0g.net',
      setup_requires=[
          'setuptools_scm',
          'setuptools-markdown',
          'wheel>=0.25.0',
      ],
      long_description_markdown_filename='README.md',
      use_scm_version={'version_scheme':'guess-next-dev'},
      include_package_data = True,
      install_requires=requirements,
      tests_require=requirements_tests,
      extras_require={'test': requirements_tests},
      dependency_links=requirements_links,
      cmdclass={
          'dist_clean': DistClean,
          'test': PyTest,
      },
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      git-repo = git_repo.repo:cli
      """,
      license='GPLv2',
      packages=find_packages(exclude=['tests']),
      test_suite='pytest',
      zip_safe=False
      )
