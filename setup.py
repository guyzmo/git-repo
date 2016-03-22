from setuptools import setup, find_packages


setup(name='git-repo',
      version='1.3',
      description='Tool for managing remote repositories from your git CLI!',
      classifiers=[
            'Development Status :: 2 - Pre-Alpha',
      ],
      keywords='git',
      url='https://github.com/guyzmo/git-repo',
      author='Bernard `Guyzmo` Pratz',
      author_email='guyzmo+git-repo@m0g.net',
      setup_requires=['setuptools-markdown'],
      long_description_markdown_filename='README.md',
      install_requires=[
            'docopt',
            'GitPython',
            'python-gitlab',
            'github3.py',
            'bitbucket-api',
      ],
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      git-repo = git_repo.repo:cli
      """,
      license='GPLv2',
      packages=find_packages(),
      # test_suite='nose.collector',
      # tests_require=['nose'],
      zip_safe=False
      )
