## Git-Repo: git services CLI utility

* To get the sources:
  * https://github.com/guyzmo/git-repo
  * https://gitlab.com/guyzmo/git-repo
  * https://bitbucket.org/guyzmo/git-repo
* Issues: https://github.com/guyzmo/git-repo/issues
* Meet the community, come chat:
  * on IRC: [#git-repo @freenode](https://webchat.freenode.net/?channels=#git-repo)
  * on Matrix: [#git-repo:matrix.org](https://riot.im/app/#/room/#git-repo:matrix.org)
  * on Gitter: [git-services/git-repo](https://gitter.im/git-services/git-repo)
* [![Issues in Ready](https://badge.waffle.io/guyzmo/git-repo.png?label=ready&title=Ready)](https://waffle.io/guyzmo/git-repo) [![Issues in Progress](https://badge.waffle.io/guyzmo/git-repo.png?label=in%20progress&title=Progress)](https://waffle.io/guyzmo/git-repo) [![Show Travis Build Status](https://travis-ci.org/guyzmo/git-repo.svg)](https://travis-ci.org/guyzmo/git-repo)
* [![Pypi Version](https://img.shields.io/pypi/v/git-repo.svg) ![Pypi Downloads](https://img.shields.io/pypi/dm/git-repo.svg)](https://pypi.python.org/pypi/git-repo)

## Looking for help

For the past few months I've been really busy coding on stuff that puts food on the table…
And sadly, I cannot give this project all the love it deserves. Which is why it's taken me months
to spend a few hours merge and release the PRs featured in this repository.

I'm still using this project daily, but I'm not having enough time to keep on putting all the
effort needed to make it shine (SSH keys, issues support…)

So I'd like to share the maintenance responsibility with someone or more people. If you're
interested, please ping me on IRC or by mail (which is in all my commits). I'm always happy
to guide through the code's design!

### Usage

#### main commands

Control your remote git hosting services from the `git` commandline. The usage is
very simple (full usage list [in the sources][1]). To clone a new project, out of GitHub, just issue:

[1]:https://github.com/guyzmo/git-repo/blob/devel/git_repo/repo.py#L4,L35

    % git hub clone guyzmo/git-repo

But that works also with a project from GitLab, Bitbucket, your own GitLab or Gogs:

    % git lab clone guyzmo/git-repo
    % git bb clone guyzmo/git-repo
    % git myprecious clone guyzmo/git-repo
    % git gg clone guyzmo/git-repo

If you want to choose the default branch to clone:

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

Also, you can open the repository's page, using the `open` command:

    % git lab open guyzmo/git-repo
    Successfully fetched branch `2` of `guyzmo/git-repo` into `request-2`!

#### Requests for merges *(aka Pull Requests aka Merge Requests)*

Once you're all set with your repository, you can check requests to merge
(aka Pull Requests on github) using the `request` command:

    % git hub request guyzmo/git-repo list
    List of open requests to merge:
    id     title                                                           URL
    2     prefer gitrepo.<target>.token > privatekey, docs                https://api.github.com/repos/guyzmo/git-repo/issues/2

And fetch it locally to check and/or amend it before merging:

    % git hub request guyzmo/git-repo fetch 2

Or you can create a request by doing a:

    % git hub request create guyzmo/git-repo myfeature master -t 'My neat feature' -m 'So much to say about that feature…'

You can create the request also by simply calling:

    % git hub request create

That command has a bit of automagic, it will:

1. lookup the namespace and project of the current branch (or at least on the `github` 
   remote, if called with `hub`), and take this as the source of the request ;
2. for the target of the request it will lookup and take:
  * the parent if current project has a parent
  * or itself, if does not ;
3. it will take the currently loaded branch for the source
4. and the default one for the target
5. call the service to ask for a request to merge from source onto target.

#### Gists or snippets

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
> have access to the tool using `git-repo hub …` or `git repo hub …`. For the
> `git hub …` call, you have to set up aliases, see below how to configure that.

#### Remotes

Traditionally, `origin` is being used as the remote name for the code hosted on a 
service, but because of the nature of `git-repo` there is no single `origin` but
it encourages to use multiple ones, and also leave you in control of wherever
`origin` points to.

This is why when you clone from a service or create a new repo on a service,
it's using a special remote that carries the name of the service:

    % git hub clone foo/bar; cd bar
    % git status -sb | head -1
    ## master...github/master
                ^^^^^^
    % git lab create bar
    % git push gitlab master

And as a bonus, each time it's adding a new remote, it's updating the `all` remote,
so that you can push your code to all your remote repositories in one command:

    % git push all master
    
Another special remote is the `upstream`. When you do a fork of a project, current
special remote with a service name will be renamed as `upstream` and the newly
forked project is now the one with the service name:

    % git lab clone foo/bar; cd bar
    % git remote
    all
    gitlab
    % git lab fork
    % git remote
    all
    gitlab
    upstream

Finally, if you want to link other existing projects, you can, the `add` command
is there for that:

    % git bb add foo/bar
    % # if the name is identical to current project, you don't need to add a name
    % git hub add
    % git gg add foo/bar gitea --alone

Use the `--alone` switch if you don't want to add that project in the `all`
special remote.

And of course the above commands is just sugar around regular git commands,
so the above can also be done with:

    % git remote add gitbucket https://gitbucket.local:8080/foo/bar
    % # the command to append the URL to the all remote, --alone skips this step
    % git remote set-url --add all https://gitbucket.local:8080/foo/bar

And to remove a remote, just do:

    % git remote remove github

### Installation

You can get the tool using pypi (use `pip3` if you have both Python2 and Python3 installed):

    % pip install git-repo

or by getting the sources and running:

    % python3 setup.py install

### Configuration

To configure `git-repo` you simply have to call the following command:

    % git repo config

and a wizard will run you through getting the authentication token for the
service, add the command alias or the name of the remote. Though, configuring
custom services is still not handled by the wizard…

But if you prefer manual configuration you'll have to tweak your
`~/.gitconfig`. For each service you've got an account on, you have to make a
section in the gitconfig:

    [gitrepo "gitlab"]
        token = YourVerySecretKey

    [gitrepo "github"]
        token = YourOtherVerySecretKey

    [gitrepo "bitbucket"]
        username = ford.prefect
        token = YourSecretAppKey

    [gitrepo "gogs"]
        fqdn = UrlOfYourGogs
        token = YourVerySecretKey

Here, we're setting the basics: just the private token. Notice that the token needed for Bitbucket are an App-token, not to be confused with an OAuth-token, which are also avaiable from the Butbucket settings.

You also have the ability to set up an alias:

    [gitrepo "bitbucket"]
        alias = bit
        username = ford.prefect
        token = YourSecretAppKey

that will change the command you use for a name you'll prefer to handle actions
for the service you use:

    % git-repo bit clone guyzmo/git-repo

Also, you can setup your own GitLab self-hosted server, using that configuration:

    [gitrepo "myprecious"]
        type = gitlab
        token = YourSuperPrivateKey
        fqdn = gitlab.example.org
        # Set this only if you use a self-signed certificate and experience problems
        insecure = true

Finally, to make it really cool, you can make a few aliases in your gitconfig:

    [alias]
        hub = repo hub
        lab = repo lab
        bb = repo bb
        perso = repo perso

So you can run the tool as a git subcommand:

    git hub clone guyzmo/git-repo

For those who like to keep all dotfiles in a git repository, it'd be horrendous to
store tokens that offer access to your social accounts in a repository… And I'm not
even talking about those who want to share your dotfiles. But don't worry, once
it's all configured, you can fire up your [favorite editor](http://www.vim.org) and
move all the `[gitrepo …]` sections into a new file, like `~/.gitconfig-repos`.

Your can run the following command to do this automagically:

    python -m git_repo.extract_config

if you want to use another path, you can change the defaults:

    python -m git_repo.extract_config ~/.gitconfig-repos ~/.gitconfig

### Configuring Gerrit

Please note: when configuration wizard will ask you for password, do not provide
your Gerrit account password, but enter `HTTP password` instead. You can setup
it on [Settings > HTTP Password page](https://review.gerrithub.io/#/settings/http-password)

You may also need to tweak your `~/.gitconfig`:
* set `ro-suffix` if your Gerrit isn't served at server root. For example, set
  `ro-suffix` to `/r` if your Gerrit is hosted at `https://review.host.com/r`
* set `ssh-port` parameter to set custom port for ssh connection to Gerrit (default: 29418)
* set `auth-type`: basic (default) or digest

### Development

For development, start a virtualenv and from within install the devel requirements:

    % virtualenv var
    % var/bin/pip install -r requirements-test.txt

and then you'll have the executable in `bin`:

    % var/bin/git-repo --help

and to run the tests:

    % var/bin/py.test --cov=git_repo --cov-report term-missing --capture=sys tests

N.B.: *Buildout is no longer supported for development*

#### Verbose running

You can repeat the `-v` argument several times to increase the level of verbosity
of `git-repo`. The more arguments you give, the more details you'll have.

* `-v` will set the debugging level to `DEBUG`, giving some execution info ;
* `-vv` will print out all the git commands that are being executed ;
* `-vvv` will give more verbose insight on the git layer ;
* `-vvvv` will output all the HTTP exchanges with the different APIs ;
* `-vvvvv` will printout how were parsed the arguments.

##### Testing

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

* `GITHUB_NAMESPACE` (which defaults to `not_configured`) is the name of the account to use on GitHub
* `GITLAB_NAMESPACE` (which defaults to `not_configured`) is the name of the account to use on GitLab
* `BITBUCKET_NAMESPACE` (which defaults to `not_configured`) is the name of the account to use on Bitbucket
* `GOGS_NAMESPACE` (which defaults to `not_configured`) is the name of the account to use on Gogs
* `PRIVATE_KEY_GITHUB` your private token you've setup on GitHub for your account
* `PRIVATE_KEY_GITLAB` your private token you've setup on GitLab for your account
* `PRIVATE_KEY_BITBUCKET` your private token you've setup on Bitbucket for your account
* `PRIVATE_KEY_GOGS` your private token you've setup on Gogs for your account

### TODO

* [x] make a `git-repo fork` action
* [x] make it possible to choose method (SSH or HTTPS)
* [x] handle default branches properly
* [x] make a nice way to push to all remotes at once
* [x] refactor the code into multiple modules
* [x] add regression tests (and actually find a smart way to implement them…)
* [x] add travis build
* [x] show a nice progress bar, while it's fetching (cf [#15](https://github.com/guyzmo/git-repo/issues/15))
* [x] add support for handling gists (cf [#12](https://github.com/guyzmo/git-repo/issues/12), cf [#13](https://github.com/guyzmo/git-repo/issues/13))
* [x] add support for handling pull requests (cf [#10](https://github.com/guyzmo/git-repo/issues/10), [#11](https://github.com/guyzmo/git-repo/issues/11))
* [x] add application token support for bitbucket (cf [#14](https://github.com/guyzmo/git-repo/issues/14))
* [x] add support for gogs (cf [#18](https://github.com/guyzmo/git-repo/issues/18))
* [x] add support for gitbucket (cf [#142](https://github.com/guyzmo/git-repo/issues/142))
* [ ] add support for managing SSH keys (cf [#22](https://github.com/guyzmo/git-repo/issues/22))
* [ ] add support for issues (cf [#104](https://github.com/guyzmo/git-repo/issues/104))
* [ ] add support for gerrit (cf [#19](https://github.com/guyzmo/git-repo/issues/19))
* [ ] do what's needed to make a nice documentation [#146](https://github.com/guyzmo/git-repo/issues/146)
* for more features, write an issue or, even better, a PR!

# Contributors

The project and original idea has been brought and is maintained by:

* Bernard [@guyzmo](https://github.com/guyzmo) Pratz — [commits](https://github.com/guyzmo/git-repo/commits?author=guyzmo)

With code contributions coming from:

* [@PyHedgehog](https://github.com/pyhedgehog) — [commits](https://github.com/guyzmo/git-repo/commits?author=pyhedgehog)
* [@guyhughes](https://github.com/guyhughes) — [commits](https://github.com/guyzmo/git-repo/commits?author=guyhughes)
* [@buaazp](https://github.com/buaazp) — [commits](https://github.com/guyzmo/git-repo/commits?author=buaazp)
* [@peterazmanov](https://github.com/peterazmanov) — [commits](https://github.com/guyzmo/git-repo/commits?author=peterazmanov)
* [@Crazybus](https://github.com/Crazybus) — [commits](https://github.com/guyzmo/git-repo/commits?author=Crazybus)
* [@rnestler](https://github.com/rnestler) — [commits](https://github.com/guyzmo/git-repo/commits/devel?author=rnestler)
* [@jayvdb](https://github.com/jayvdb) — [commits](https://github.com/guyzmo/git-repo/commits/devel?author=jayvdb)
* [@kounoike](https://github.com/kounoike) — [commits](https://github.com/guyzmo/git-repo/commits/devel?author=kounoike)
* [@AmandaCameron](https://github.com/AmandaCameron) — [commits](https://github.com/guyzmo/git-repo/commits/devel?author=AmandaCameron)
* [@fa7ad](https://github.com/fa7ad) — [commits](https://github.com/guyzmo/git-repo/commits/devel?author=fa7ad)

### License

    Copyright ©2016,2017 Bernard `Guyzmo` Pratz <guyzmo+git-repo+pub@m0g.net>

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
