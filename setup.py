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

# Use buildout's path for eggs
def get_egg_cache_dir(self):
    egg_cache_dir = os.path.join(os.curdir, 'var', 'eggs')
    if not os.path.exists(egg_cache_dir):
        os.makedirs(egg_cache_dir, exist_ok=True)
    return egg_cache_dir
dist.Distribution.get_egg_cache_dir = get_egg_cache_dir


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


class Buildout(Command):
    description = 'Running buildout on the project'
    user_options = []

    def initialize_options(self): pass
    def finalize_options(self): pass

    def run(self):
        try:
            from zc.buildout.buildout import main
        except ImportError:
            print('Please install buildout!\n  pip install zc.buildout')
            sys.exit(1)
        errno = main(sys.argv[sys.argv.index('buildout')+1:])
        if errno == 0:
            print('Now you can run tests using: bin/py.test')
            print('Now you can test current code using: bin/git-repo')
            print('Thank you 🍻')
        sys.exit(errno)


requirements_links = []

def requirements(spec=None):
    spec = '{}{}.txt'.format('requirements',
            '-'+spec if spec else '')
    requires = []

    requirements = pip.req.parse_requirements(
        spec, session=pip.download.PipSession())

    for item in requirements:
        if getattr(item, 'link', None):
            requirements_links.append(str(item.link))
        if item.req:
            requires.append(str(item.req))

    return requires


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
      install_requires=requirements(),
      tests_require=requirements('test'),
      dependency_links=requirements_links,
      cmdclass={
          'buildout': Buildout,
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
