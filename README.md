## Git-Repo: git services CLI utility

* To get the sources:
  * https://github.com/guyzmo/git-repo
  * https://gitlab.com/guyzmo/git-repo
  * https://bitbucket.org/guyzmo/git-repo
* Issues: https://github.com/guyzmo/git-repo/issues
* [![Show Travis Build Status](https://travis-ci.org/guyzmo/git-repo.svg)](https://travis-ci.org/guyzmo/git-repo)
* [![Pypi Version](https://img.shields.io/pypi/v/git-repo.svg) ![Pypi Downloads](https://img.shields.io/pypi/dm/git-repo.svg)](https://pypi.python.org/pypi/git-repo)

### Usage

Control your remote git hosting services from the `git` commandline. The usage is
very simple. To clone a new project, out of github, just issue:

    % git hub clone guyzmo/git-repo

But that works also with a project from gitlab, bitbucket, or your own gitlab:

    % git lab clone guyzmo/git-repo
    % git bb clone guyzmo/git-repo
    % git myprecious clone guyzmo/git-repo

If you want to can choose the default branch to clone:

    % git lab clone guyzmo/git-repo master

Though sometimes, as you're starting a new project, you want to create a new
repository to push to:

    % git hub create guyzmo/git-repo

actually the namespace is facultative, as per default you can (and want to)
only create new repositories within your own account.

You might also want to add an existing remote ref to your workspace, and that
can be easily done with:

    % git lab add guyzmo/git-repo

Which will add `https://gitlab.com/guyzmo/git-repo` as the `gitlab` remote!

Also, you can fork a repository using:

    % git hub fork neovim/neovim

and of course, you can delete it using:

    % git bb delete guyzmo/git-repo

Once you're all set with your repository, you can check requests to merge 
(aka Pull Requests on github) using the `request` command:

    % git hub request guyzmo/git-repo list
    List of open requests to merge:
    id     title                                                           URL
    2     prefer gitrepo.<target>.token > privatekey, docs                https://api.github.com/repos/guyzmo/git-repo/issues/2

And fetch it locally to check and/or amend it before merging:

    % git hub request guyzmo/git-repo fetch 2

Finally, you can open the repository's page, using the `open` command:

    % git lab open guyzmo/git-repo
    Successfully fetched branch `2` of `guyzmo/git-repo` into `request-2`!

Finally, another extra feature you can play with is the gist handling:

    % git hub gist list
    id                                                              title
    https://gist.github.com/4a0dd9177524b2b125e9166640666737        This is a test gist

Then you can list files within it:

    % git hub gist list a7ce4fddba7744ddf335
    language         size  name
    Python           1048  unicode_combined.py
    % git hub -v gist list https://gist.github.com/4a0dd9177524b2b125e9166640666737
    language         size  name
    Markdown         16    README.md
    Text             14    LICENSE
    reStructuredText 17    README.rst

to output it locally, you can use the fetch command (and specify the file if there's more than one):

    % git hub gist fetch https://gist.github.com/a7ce4fddba7744ddf335 > mygist.py
    % git hub gist fetch 4a0dd9177524b2b125e9166640666737 LICENSE > LICENSE_from_gist

but for more thorough modifications or consulting, you can as well clone it:

    % git hub gist clone 4a0dd9177524b2b125e9166640666737
    Pulling from github |████████████████████████████████|
    Successfully cloned `4a0dd9177524b2b125e9166640666737` into `./4a0dd9177524b2b125e9166640666737`!

And when you're done you just get rid of it:

    % git hub gist -f delete 4a0dd9177524b2b125e9166640666737
    Successfully deleted gist!

> *Nota Bene*: Thanks to `git` CLI flexibility, by installing `git-repo` you directly
> have acces to the tool using `git-repo hub …` or `git repo hub …`. For the
> `git hub …` call, you have to set up aliases, see below how to configure that.

And as a bonus, each time it's adding a new remote, it's updating the `all` remote,
so that you can push your code to all your remote repositories in one command:

    % git push all master

### Installation

You can get the tool using pypi:

    % pip install git-repo

or by getting the sources and running:

    % python3 setup.py install

### Configuration

To configure `git-repo` you need to tweak your `~/.gitconfig`. For each service
you've got an account on, you have to make a section in the gitconfig:

    [gitrepo "gitlab"]
        token = YourVerySecretKey

    [gitrepo "github"]
        token = YourOtherVerySecretKey

    [gitrepo "bitbucket"]
        token = username:password

Here, we're setting the basics: just the private token. You'll notice that for bitbucket
the private token is your username and password seperated by a column. That's because
bitbucket does not offer throw away private tokens for tools (I might implement BB's OAuth
at some point).

You also have the ability to set up an alias:

    [gitrepo "bitbucket"]
        alias = bit
        token = username:password

that will change the command you use for a name you'll prefer to handle actions
for the service you use:

    % git-repo bit clone guyzmo/git-repo

Also, you can setup your own gitlab self-hosted server, using that configuration:

    [gitrepo "myprecious"]
        type = gitlab
        token = YourSuperPrivateKey
        fqdn = gitlab.example.org

Finally, to make it really cool, you can make a few aliases in your gitconfig:

    [alias]
        hub = repo hub
        lab = repo lab
        bb = repo bb
        perso = repo perso

So you can run the tool as a git subcommand:

    git hub clone guyzmo/git-repo

### Development

For development, I like to use `buildout`, and the repository is already configured
for that. All you have to do, is install buildout, and then call it from the root of 
the repository:

    % pip install zc.buildout
    % buildout

and then you'll have the executable in `bin`:

    % bin/git-repo --help

To run the tests:

    % bin/py.test

You can use the following options for py.test to help you debug when tests fail:

* `-v` will show more details upon errors
* `-x` will stop upon the first failure
* `--pdb` will launch the debugger where an exception has been launched


The tests use recordings of exchanged HTTP data, so that we don't need real credentials
and a real connection, when testing the API on minor changes. Those recordings are
called cassettes, thanks to the [betamax](https://github.com/sigmavirus24/betamax) framework
being in use in the test suites.

When running existing tests, based on the provided cassettes, you don't need any 
setting. Also, if you've got a configuration in `~/.gitconfig`, the tests will use
them. Anyway, you can use environment variables for those settings (environment
variables will have precedence over the configuration settings):

To use your own credentials, you can setup the following environment variables:

* `GITHUB_NAMESPACE` (which defaults to `not_configured`) is the name of the account to use on github
* `GITLAB_NAMESPACE` (which defaults to `not_configured`) is the name of the account to use on gitlab 
* `BITBUCKET_NAMESPACE` (which defaults to `not_configured`) is the name of the account to use on bitbucket
* `PRIVATE_KEY_GITHUB` your private token you've setup on github for your account
* `PRIVATE_KEY_GITLAB` your private token you've setup on gitlab for your account
* `PRIVATE_KEY_BITBUCKET` your private token you've setup on bitbucket for your account

### TODO

* [x] make a `git-repo fork` action
* [x] make it possible to choose method (SSH or HTTPS)
* [x] handle default branches properly
* [x] make a nice way to push to all remotes at once
* [x] refactor the code into multiple modules
* [x] add regression tests (and actually find a smart way to implement them…)
* [x] add travis build
* [ ] add support for handling gists
  * [x] github support
  * [ ] gitlab support
  * [ ] bitbucket support
* [ ] add support for handling pull requests
  * [x] list them
  * [x] fetch them as local branches
  * [x] github support
  * [ ] gitlab support
  * [ ] bitbucket support
* [ ] add OAuth support for bitbucket
* [ ] show a nice progress bar, while it's fetching
  * partly implemented: the issue looks like that gitpython expects output from git
    on stderr, whereas it's outputing on stdout.
* [ ] do what's needed to make a nice documentation (if possible in markdown !@#$)
* for more features, write an issue or, even better, a PR!

### License

    Copyright ⓒ Bernard `Guyzmo` Pratz <guyzmo+git-repo@m0g.net>

    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 2
    of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

See the LICENSE file for the full license.

♥
