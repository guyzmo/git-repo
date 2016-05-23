from setuptools import setup, find_packages

import sys

if sys.version_info.major < 3:
    print('Please install with python version 3')
    sys.exit(1)

from distutils.core import Command
from distutils.core import setup

class dist_clean(Command):
    description = 'Clean the repository from all buildout stuff'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


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

setup(name='git-repo',
      version='1.6.0',
      description='Tool for managing remote repositories from your git CLI!',
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
          'setuptools-markdown'
      ],
      long_description_markdown_filename='README.md',
      include_package_data = True,
      install_requires=[
            'docopt',
            'GitPython==2.0.2',
            'progress==1.2',
            'python-gitlab==0.13',
            'github3.py==0.9.5',
            'bitbucket-api==0.5.0',
      ],
      cmdclass={'dist_clean': dist_clean},
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      git-repo = git_repo.repo:cli
      """,
      license='GPLv2',
      packages=find_packages(exclude=['tests']),
      test_suite='pytest',
      tests_require=[
          'pytest==2.9.1',
          'pytest-cov',
          'pytest-sugar',
          'pytest-catchlog',
          'pytest-datadir-ng',
      ],
      zip_safe=False
      )
